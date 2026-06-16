import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import webservice.dependencies as dependencies
from webservice.routers.chat import router as chat_router
from webservice.routers.courses import router as course_router
from webservice.routers.research import router as research_router
from webservice.routers.profile import router as profile_router
from webservice.profile_store import init_store
from webservice.agent import ChatAgent

from autonomy.rag.indexer import run_indexing
from autonomy.rag.vector_store import get_client, get_collection

from contextlib import asynccontextmanager

from autonomy.agent.react_agent import ReActAgent
from autonomy.llm.openai_llm import OpenAILLM
from autonomy.llm.factory import get_llm
from autonomy.tools.base import ToolkitManager 

from dotenv import load_dotenv
from langchain_tavily import TavilySearch
import os
import statistics

from pydantic import BaseModel
from fastapi import APIRouter
from webservice.routers.research import router as research_router, run_research_query, ResearchRequest
import json
import re


from autonomy.tools.gophergrades_api import gophergrades_search, gophergrades_class, gophergrades_prof, gophergrades_dept
from autonomy.tools.umn_rooms_tool import umn_room_booking
from webservice.profile_store import init_store, get_profile, save_profile
from webservice.personalization import build_personalized_prompt


# History Storage
# """
# This defines where we are storing the conversation history into.
# Will be using as a memory cache, to continue dialogue with agent.
# """
DATA_DIR = "/app/data" # where the file will be stored
os.makedirs(DATA_DIR, exist_ok=True) # makes directory if doesn't exist, nothing if does exist
CONVERSATION_FILE = os.path.join(DATA_DIR, "conversations.json") # full path of where JSON file is stored


# GopherGrades Testing Endpoint
class CourseLookupRequest(BaseModel):
    query: str

class ProfessorLookupRequest(BaseModel):
    name: str

# class ChatRequest(BaseModel):
#     message: str

class DepartmentLookupRequest(BaseModel):
    dept: str

class ChatRequest(BaseModel):

    message: str

    # ensures loading the correct history and not all
    conversation_id: int | None = None # makes it optional, provide stability to frontend, since no history may exist
    user_id: str | None = None  # optional — used to load profile context


class ProfileRequest(BaseModel):
    user_id: str
    major: str = ""
    level: str = ""
    year: str = ""
    personalization_notes: str = ""


def _parse_srt_vals(raw):
    if raw is None or raw == "null":
        return None

    if isinstance(raw, dict):
        return raw

    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return None


def _sum_grade_counts(grades):
    if not grades:
        return 0

    return sum(value for value in grades.values() if isinstance(value, (int, float)))


def _compute_course_metrics(course):
    grades = course.get("total_grades") or {}
    total_outcomes = _sum_grade_counts(grades)
    srt_vals = _parse_srt_vals(course.get("srt_vals"))

    recommend = srt_vals.get("RECC") if srt_vals else None
    responses = srt_vals.get("RESP") if srt_vals else None

    high_grade_rate = None
    challenge_rate = None
    withdraw_rate = None

    if total_outcomes > 0:
        high_grade_rate = (
            grades.get("A", 0) + grades.get("A-", 0) + grades.get("B+", 0)
        ) / total_outcomes
        challenging_count = (
            grades.get("C-", 0)
            + grades.get("D+", 0)
            + grades.get("D", 0)
            + grades.get("F", 0)
            + grades.get("W", 0)
            + grades.get("N", 0)
        )
        # Bayesian smoothing: blend observed rate toward a prior (7%) weighted
        # by 100 pseudo-students. Small classes get pulled toward the prior;
        # large classes are barely affected.
        _PRIOR_RATE = 0.07
        _PRIOR_WEIGHT = 100
        challenge_rate = (challenging_count + _PRIOR_WEIGHT * _PRIOR_RATE) / (total_outcomes + _PRIOR_WEIGHT)
        withdraw_rate = grades.get("W", 0) / total_outcomes

    return {
        "recommend": recommend,
        "responses": responses,
        "deep_understanding": srt_vals.get("DEEP_UND") if srt_vals else None,
        "stimulating_interest": srt_vals.get("STIM_INT") if srt_vals else None,
        "technical_effectiveness": srt_vals.get("TECH_EFF") if srt_vals else None,
        "accessible_support": srt_vals.get("ACC_SUP") if srt_vals else None,
        "effort": srt_vals.get("EFFORT") if srt_vals else None,
        "grading_standards": srt_vals.get("GRAD_STAND") if srt_vals else None,
        "high_grade_rate": high_grade_rate,
        "challenge_rate": challenge_rate,
        "withdraw_rate": withdraw_rate,
    }


KNOWN_REQUIRED_DEPT_COURSES = {
    "CSCI": {"1133", "1913", "1933", "2011", "2021", "2033", "2041", "4041"},
    "MATH": {"1271", "1272", "1371", "1372", "1571", "1572", "2243", "2263", "2373", "2374", "3283W"},
    "STAT": {"3011", "3021", "3032", "5101"},
    "BIOL": {"1951", "1961", "2003", "2004"},
    "CHEM": {"1015", "1061", "1062", "2301", "2302"},
    "PHYS": {"1301W", "1302W", "1401V", "1402V"},
}


def _course_level(course_num):
    match = re.search(r"(\d{4})", str(course_num))
    if not match:
        return None
    return int(match.group(1))


def _is_popular_elective_candidate(course, dept_code):
    course_num = str(course.get("course_num") or "").upper()
    title = str(course.get("title") or "").lower()
    description = str(course.get("description") or "").lower()
    level = _course_level(course_num)
    combined = f"{title} {description}"

    if level is None or level < 3000:
        return False

    if course_num in KNOWN_REQUIRED_DEPT_COURSES.get(dept_code, set()):
        return False

    core_hints = (
        "introduction to",
        "intro to",
        "foundations",
        "fundamentals",
        "elementary",
        "principles",
        "basic ",
        "corequisite",
        "required",
    )
    if any(hint in combined for hint in core_hints):
        return False

    return True


def _normalize_department_course(course):
    return {
        "id": course.get("id"),
        "course_num": course.get("course_num", ""),
        "title": course.get("class_desc", ""),
        "description": course.get("onestop_desc", ""),
        "catalog_url": course.get("onestop", ""),
        "credits": {
            "min": course.get("cred_min"),
            "max": course.get("cred_max"),
        },
        "total_students": course.get("total_students", 0),
        "grades": course.get("total_grades") or {},
        "metrics": _compute_course_metrics(course),
    }


def _build_department_summary(courses):
    student_counts = [course.get("total_students", 0) for course in courses]
    recommend_values = [
        course["metrics"]["recommend"]
        for course in courses
        if course["metrics"]["recommend"] is not None
    ]

    return {
        "course_count": len(courses),
        "total_students": sum(student_counts),
        "median_course_size": int(statistics.median(student_counts)) if student_counts else 0,
        "courses_with_srt": len(recommend_values),
        "avg_recommend": (
            round(sum(recommend_values) / len(recommend_values), 3)
            if recommend_values
            else None
        ),
    }


def _build_department_featured(courses, dept_code):
    popular = sorted(
        courses,
        key=lambda course: course.get("total_students", 0),
        reverse=True,
    )[:8]

    best_rated_pool = [
        course
        for course in courses
        if course["metrics"]["recommend"] is not None
        and (course["metrics"]["responses"] or 0) >= 50
    ]
    best_rated = sorted(
        best_rated_pool,
        key=lambda course: (
            course["metrics"]["recommend"],
            course["metrics"]["responses"] or 0,
        ),
        reverse=True,
    )[:8]

    elective_pool = [
        course
        for course in courses
        if _is_popular_elective_candidate(course, dept_code)
    ]
    popular_electives = sorted(
        elective_pool,
        key=lambda course: (
            course.get("total_students", 0),
            course["metrics"]["recommend"] or 0,
        ),
        reverse=True,
    )[:8]

    return {
        "popular": popular,
        "best_rated": best_rated,
        "popular_electives": popular_electives,
    }

class ChatAgent:
    def __init__(self, name="Assistant"):
        self.name = name

        load_dotenv()
        os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

        self.llm = get_llm().get_model()
        search_tool = TavilySearch(max_results=5, topic="general", search_depth="advanced", include_domains=["umn.edu", "reddit.com"])

        self.toolkit = ToolkitManager()

        self.toolkit.register_tools([search_tool], type="other")

        # Adding gopherGrade tools to agent
        gopherGradeTools = [gophergrades_search, gophergrades_class, gophergrades_prof, gophergrades_dept]
        self.toolkit.register_tools(gopherGradeTools, type="retriever")

        # Adding UMN room booking tool
        self.toolkit.register_tool(umn_room_booking, type="other")

        self.react_agent = ReActAgent(llm=self.llm, toolkit=self.toolkit,
                                      system_prompt=(
                                          "You are GopherGPT, a helpful assistant for University of Minnesota (UMN) students. "
                                          "You help with courses, professors, grade distributions, GPA trends, and campus resources. "
                                          "\n\nTOOL USAGE:"
                                          "\n- gophergrades_search: Use for free-text searches (topic, professor name, partial course name). Returns matching courses and instructors with IDs."
                                          "\n- gophergrades_class: Use this to get a course's full data — grade distribution, SRT ratings, AND the list of professors who teach it. "
                                          "If someone asks 'who teaches MATH 1271' or 'who teaches CSCI 1933', call gophergrades_class('MATH1271') — the professor list is in the response. "
                                          "Input must be a code with no spaces like 'MATH1271' or 'CSCI1933'."
                                          "\n- gophergrades_prof: Use to get a specific professor's full profile. Get the prof code from gophergrades_class or gophergrades_search results — never guess the code."
                                          "\n- gophergrades_dept: Use when asked about a full department (e.g. 'tell me about the CSCI department'). "
                                          "Input is a dept code like 'CSCI'. The response is large — summarize the highlights: top courses, total students, avg recommend score. Do NOT dump the full list."
                                          "\n- umn_room_booking: Use when a user asks about booking, reserving, finding rooms/study spaces, OR getting directions to a specific UMN building. Input is ONE building name. Always include the directions.google_maps and directions.campus_map links in your reply."
                                          "\n- tavily_search: Use for general UMN questions (campus life, buildings, events, resources) not covered by GopherGrades or other tools."
                                          "\n\nSTUDY SPACE QUESTIONS (general — no specific building named):"
                                          "\n- When a user asks 'where should I study', 'where are study spaces', or similar general questions, do NOT call umn_room_booking for a single building."
                                          "\n- Instead, respond with a grouped list using this EXACT format — category headers must be standalone bold lines (NOT bullet points), buildings are bullet points underneath:"
                                          "\n\n**Quiet/Solo Study**"
                                          "\n- **Walter Library**: Silent floors, individual desks. [Google Maps](https://www.google.com/maps/search/Walter+Library+University+of+Minnesota) | [Campus Map](https://campusmaps.umn.edu/walter-library)"
                                          "\n- **Wilson Library**: Private carrels, very quiet. [Google Maps](https://www.google.com/maps/search/Wilson+Library+University+of+Minnesota) | [Campus Map](https://campusmaps.umn.edu/wilson-library)"
                                          "\n- **Andersen Library**: Calm, less crowded. [Google Maps](https://www.google.com/maps/search/Andersen+Library+University+of+Minnesota) | [Campus Map](https://campusmaps.umn.edu/andersen-library)"
                                          "\n\n**Group Study**"
                                          "\n- **Walter Library**: Bookable group rooms. [Google Maps](https://www.google.com/maps/search/Walter+Library+University+of+Minnesota) | [Campus Map](https://campusmaps.umn.edu/walter-library) | [Reserve a Room](https://libcal.lib.umn.edu/spaces?lid=3604)"
                                          "\n- **Coffman Memorial Union**: Lounges + group rooms. [Google Maps](https://www.google.com/maps/search/Coffman+Memorial+Union+University+of+Minnesota) | [Campus Map](https://campusmaps.umn.edu/coffman-memorial-union)"
                                          "\n- **STSS Building**: Open study areas. [Google Maps](https://www.google.com/maps/search/Science+Teaching+Student+Services+University+of+Minnesota) | [Campus Map](https://campusmaps.umn.edu/science-teaching-student-services)"
                                          "\n\n**24/7 or Late Night**"
                                          "\n- **Bruininks Hall**: Atrium open late. [Google Maps](https://www.google.com/maps/search/Bruininks+Hall+University+of+Minnesota) | [Campus Map](https://campusmaps.umn.edu/bruininks-hall)"
                                          "\n- **Coffman Memorial Union**: Some areas open late. [Google Maps](https://www.google.com/maps/search/Coffman+Memorial+Union+University+of+Minnesota) | [Campus Map](https://campusmaps.umn.edu/coffman-memorial-union)"
                                          "\n- **Health Sciences Library**: Extended hours. [Google Maps](https://www.google.com/maps/search/Health+Sciences+Library+University+of+Minnesota) | [Campus Map](https://campusmaps.umn.edu/health-sciences-library)"
                                          "\n\n**Tech / Computer Access**"
                                          "\n- **Lind Hall**: Computer labs. [Google Maps](https://www.google.com/maps/search/Lind+Hall+University+of+Minnesota) | [Campus Map](https://campusmaps.umn.edu/lind-hall)"
                                          "\n- **Keller Hall**: CSE student resources. [Google Maps](https://www.google.com/maps/search/Keller+Hall+University+of+Minnesota) | [Campus Map](https://campusmaps.umn.edu/keller-hall)"
                                          "\n\n**St. Paul Campus**"
                                          "\n- **Magrath Library**: Cozy, uncrowded. [Google Maps](https://www.google.com/maps/search/Magrath+Library+University+of+Minnesota) | [Campus Map](https://campusmaps.umn.edu/magrath-library) | [Reserve a Room](https://libcal.lib.umn.edu/spaces?lid=3607)"
                                          "\n\nBrowse all available spaces in real time at [UMN Study Space Finder](https://studyspace.umn.edu)."
                                          "\n\nCOURSE RECOMMENDATIONS:"
                                          "\n- If the user mentions they are currently enrolled in or planning to take a course, treat ALL of that course's prerequisites as already completed. Do NOT recommend them."
                                          "\n- If the user mentions courses they have already taken (e.g. in their profile notes), never recommend those courses."
                                          "\n- When recommending a course that has prerequisites, only list prereqs the user has NOT clearly already satisfied."
                                          "\n- Example: if a user is enrolled in CSCI 4511W (which requires CSCI 4041), never recommend CSCI 4041 — they must have it."
                                          "\n\nRESPONSE STYLE:"
                                          "\n- Be concise and direct. Lead with the most useful insight."
                                          "\n- For grade data: highlight A/B rates, average GPA context, and any standout patterns."
                                          "\n- For professors: mention their rating, courses taught, and grade tendencies."
                                          "\n- Use bullet points or numbered lists when presenting multiple items."
                                          "\n- Give concrete recommendations when asked (e.g. which section to take, which prof is better)."
                                          "\n- Never say 'I don't have access' — use your tools first."
                                          "\n- If a user asks about a full department (e.g. 'tell me about the CSCI department'), "
                                          "do NOT attempt to retrieve department-wide data. Instead, let them know they can explore "
                                          "the Department Explorer tab in the sidebar for full department breakdowns."
                                      ))

    # def invoke(self, message: str) -> str:
    #     """
    #     Replace this method with your LLM/agent logic.
    #     For now, it just echoes back the message.
    #     """
    #     final_state = self.react_agent.invoke_agent({"messages": [{"role": "user", "content": message}]})
    #     generation = final_state["messages"][-1].content
    #     return generation
    
    def invoke(self, message: str, history: list = []) -> str: # added new param "history", which accepts list of prior messages, default is empty (no history)
        """ 
        Replaced the previous method above, this should maintain agent memory/cache
        Allowing for back-and-forth communication, instead of monologue
        """

        # Cap history to last 10 messages to avoid context overflow
        capped_history = history[-10:] if len(history) > 10 else history

        # prepends all prior messages to pass into agent
        messages = capped_history + [{"role": "user", "content": message}]

        # runs agent with full history instead of current
        final_state = self.react_agent.invoke_agent({"messages": messages})

        # grabs agent final response from output, last thought, most refined answer.
        generation = final_state["messages"][-1].content

        # sends response to endpoint
        return generation
    

# History Classes

class ConversationRequest(BaseModel):
    id: int
    title: str
    messages: list


gopher_assistant  = None

@asynccontextmanager
async def lifespan_function(app: FastAPI):
    """
    Handles app startup and shutdown — initializes the agent, wires dependencies, and connects to ChromaDB.

    Args:
        app: the FastAPI application instance
    """
    
    init_store()
    dependencies.gopher_assistant = ChatAgent()

    try:
        get_client()
        print("ChromaDB connected successfully.")

        collection = get_collection()

        if collection.count() == 0:
            print("Collection is empty — running indexer...")
            asyncio.create_task(run_indexing())

    except Exception as e:
        print(f"WARNING: ChromaDB connection failed: {e}")

    yield


app = FastAPI(lifespan=lifespan_function)
app.add_middleware(CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(research_router)
app.include_router(chat_router)
app.include_router(course_router)
app.include_router(profile_router)


@app.get("/")
def root():
    """
    Health check endpoint.

    Returns:
        a dict with a welcome message confirming the service is running
    """
    return {"message": "The greatest openai wrapper ever made."}

def extract_course_codes(text):
    """Extract normalized UMN course codes (e.g. CSCI4041, CSCI3081W) from a message."""
    pattern = r'\b([A-Z]{2,6})\s*(\d{4}[A-Z]?)\b'
    seen = []
    for m in re.finditer(pattern, text.upper()):
        code = f"{m.group(1)}{m.group(2)}"
        if code not in seen:
            seen.append(code)
    return seen


def extract_prof_names(message):
    """Extract two professor name candidates from a compare request."""
    m = re.search(
        r'compare\s+(?:professors?\s+|profs?\s+)?(.+?)\s+(?:and|vs\.?|versus)\s+(?:professors?\s+|profs?\s+)?(.+?)(?:\s*[\?.]?$)',
        message, re.IGNORECASE
    )
    if not m:
        return []
    name1 = m.group(1).strip().rstrip(".,?!")
    name2 = m.group(2).strip().rstrip(".,?!")
    # Skip if either looks like a course code
    if re.match(r'^[A-Za-z]{2,6}\s*\d{4}', name1) or re.match(r'^[A-Za-z]{2,6}\s*\d{4}', name2):
        return []
    if len(name1) < 3 or len(name2) < 3:
        return []
    return [name1, name2]


def _search_prof_code(name):
    """Search for a professor by name, return (code, display_name) or None."""
    import logging
    log = logging.getLogger(__name__)
    try:
        raw = gophergrades_search.invoke(name)
        result = json.loads(raw)
        log.info("Prof search for %r: %s", name, json.dumps(result)[:600])

        # Walk all possible shapes the API might return
        candidates = []

        def _extract_instructors(obj):
            if isinstance(obj, dict):
                for key in ("instructors", "professors", "instructor", "professor"):
                    val = obj.get(key)
                    if isinstance(val, list):
                        candidates.extend(val)
                for key in ("data", "results"):
                    if isinstance(obj.get(key), (dict, list)):
                        _extract_instructors(obj[key])
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, dict):
                        # item itself might be an instructor record
                        if any(k in item for k in ("instructor_id", "prof_id", "slug", "full_name")):
                            candidates.append(item)
                        else:
                            _extract_instructors(item)

        _extract_instructors(result)
        log.info("Prof candidates for %r: %s", name, json.dumps(candidates)[:400])

        if candidates:
            first = candidates[0]
            code = (
                first.get("instructor_id")
                or first.get("prof_id")
                or first.get("id")
                or first.get("slug")
                or first.get("code")
            )
            display = (
                first.get("full_name")
                or first.get("name")
                or first.get("instructor_name")
                or name
            )
            if code:
                return str(code), display
    except Exception as e:
        import logging as _log
        _log.getLogger(__name__).exception("Prof search failed for %r", name)
    return None


def is_research_followup(message, history):
    """Returns True if this looks like a follow-up to a prior research query."""
    if not re.match(r'^(what|how)\s+about|^and\b|^what if', message.strip(), re.IGNORECASE):
        return False
    recent = history[-6:] if len(history) > 6 else history
    return any(re.search(r'rea?sea?rch', msg["content"].lower()) for msg in recent)


def build_research_query(current_message, history):
    """Construct a full research query from a follow-up message using prior context."""
    for msg in reversed(history):
        if msg["role"] == "user" and re.search(r'rea?sea?rch', msg["content"].lower()):
            # Extract the new subject from the follow-up (e.g. "what about for biology" → "biology")
            m = re.search(r'(?:for|about|in)\s+([\w\s]+?)(?:\?|$)', current_message, re.IGNORECASE)
            if m:
                subject = m.group(1).strip()
                return f"research opportunities for {subject} at University of Minnesota"
            break
    return current_message


def _enrich_research_query(raw_query: str, profile: dict) -> str:
    """Make a research query more specific using profile context and UMN-specific terms."""
    query = raw_query.strip()

    # Add major from profile if not already in the query
    major = (profile.get("major") or "").strip()
    if major and major.lower() not in query.lower():
        query = f"{query} {major}"

    # Add specificity terms if the query is generic
    generic_terms = ["research", "research opportunities", "research opportunity"]
    if query.lower() in generic_terms or re.match(r'^research\s*(opportunities?|programs?)?\s*$', query.lower()):
        query = f"undergraduate research opportunities programs apply University of Minnesota"
        if major:
            query += f" {major}"
    elif re.search(r'research', query, re.IGNORECASE):
        # Already has research in it — ensure UMN context and add specificity
        if "university of minnesota" not in query.lower() and "umn" not in query.lower():
            query += " University of Minnesota"
        if not any(t in query.lower() for t in ["apply", "program", "lab", "undergraduate", "faculty"]):
            query += " undergraduate program apply"

    return query


# responsible for loading/retrieving chat messages
@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    global gopher_assistant
    if gopher_assistant is None:
        return {"error": "Agent not initialized."}

    message = request.message.lower()

    # Load profile context if user_id provided
    profile_context = ""
    if request.user_id:
        profile = get_profile(request.user_id)
        profile_context = build_personalized_prompt(profile)

    # Loads the conversation history from file "app/data"
    history = []
    if request.conversation_id is not None and os.path.exists(CONVERSATION_FILE):
        with open(CONVERSATION_FILE, "r") as file:
            conversations = json.load(file)
        match = next((c for c in conversations if c["id"] == request.conversation_id), None)
        if match:
            history = [{
                "role": "user" if msg["isUser"] else "assistant",
                "content": msg["text"]}
                for msg in match["messages"]
            ]

    if re.search(r'rea?sea?rch', message) or is_research_followup(message, history):
        raw_query = request.message if re.search(r'rea?sea?rch', message) else build_research_query(message, history)
        query = _enrich_research_query(raw_query, get_profile(request.user_id) if request.user_id else {})
        research_data = run_research_query(ResearchRequest(query=query, max_results=10))

        # Deduplicate by domain, but allow up to 2 results per domain for rich sources
        domain_counts: dict = {}
        unique_results = []
        for r in research_data.results:
            domain = re.sub(r'^https?://([^/]+).*', r'\1', r.url)
            count = domain_counts.get(domain, 0)
            if count < 2:
                domain_counts[domain] = count + 1
                unique_results.append(r)

        summary_text = summarize_research_text(research_data.summary, limit=200)

        return {
            "response": "Here's a research snapshot with the strongest matches I found.",
            "content": [
                {
                    "type": "research",
                    "summary": summary_text,
                    "results": [
                        {
                            "title": summarize_research_text(result.title, limit=90),
                            "url": result.url,
                            "snippet": summarize_research_text(result.snippet, limit=160)
                        }
                        for result in unique_results
                    ][:6]
                }
            ]
        }

    # Detect professor comparison requests
    if "compare" in message and re.search(r'\bprof(essor)?\b', message, re.IGNORECASE):
        prof_names = extract_prof_names(request.message)
        if len(prof_names) == 2:
            import logging as _plog
            _plog.getLogger(__name__).info("Prof compare names: %s", prof_names)
            profs = []
            for pname in prof_names:
                found = _search_prof_code(pname)
                _plog.getLogger(__name__).info("Found code for %r: %s", pname, found)
                if found:
                    code, display = found
                    try:
                        prof_result = json.loads(gophergrades_prof.invoke(code))
                        _plog.getLogger(__name__).info("Prof result for %r (%s): %s", display, code, json.dumps(prof_result)[:600])
                        # Accept data whether it's nested under "data" or at the top level
                        data = prof_result.get("data") or prof_result
                        profs.append({"name": display, "code": code, "data": data})
                    except Exception:
                        _plog.getLogger(__name__).exception("gophergrades_prof failed for code %r", code)
            if len(profs) >= 1:
                guided_message = (
                    request.message
                    + "\n\n[System: Grade distributions and SRT ratings for each professor will be shown visually. "
                    "Write 2-3 sentences max with a high-level comparison or recommendation. "
                    "Do NOT mention specific numbers — those are already in the charts. "
                    "Do NOT say there was any issue retrieving data or that information is unavailable — just give your comparison.]"
                )
                try:
                    ai_summary = gopher_assistant.invoke(guided_message, history=history)
                except Exception:
                    ai_summary = ""
                return {
                    "response": "",
                    "content": [{"type": "prof_compare", "profs": profs, "summary": ai_summary}]
                }

    # Detect course comparison requests
    course_codes = extract_course_codes(request.message)
    is_compare_request = "compare" in message and len(course_codes) >= 1

    if is_compare_request or len(course_codes) >= 2:
        courses = []
        for code in course_codes[:2]:
            try:
                class_result = json.loads(gophergrades_class.invoke(code))
                if class_result.get("data"):
                    courses.append({
                        "code": code,
                        "data": class_result["data"]
                    })
            except Exception:
                pass

        if courses:
            guided_message = (
                request.message
                + "\n\n[System: Grade distributions and SRT ratings will be shown visually. "
                "Write 2-3 sentences max giving a high-level insight or recommendation. "
                "Do NOT mention any numbers, grades, or ratings — those are already in the charts.]"
            )
            try:
                ai_summary = gopher_assistant.invoke(guided_message, history=history)
            except Exception:
                ai_summary = ""
            return {
                "response": "",
                "content": [{"type": "compare", "courses": courses, "summary": ai_summary}]
            }

    full_message = f"{profile_context}\n\nUser message:\n{request.message}" if profile_context else request.message
    try:
        response = gopher_assistant.invoke(full_message, history=history)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Agent invocation failed")
        return {
            "response": "I ran into an issue processing your request. Please try again or rephrase your question.",
            "content": []
        }
    return {
        "response": response,
        "content": []
    }

@app.get("/debug/prof")
def debug_prof(name: str):
    """Debug endpoint — returns raw search + prof data for a given name."""
    search_raw = json.loads(gophergrades_search.invoke(name))
    found = _search_prof_code(name)
    prof_raw = None
    if found:
        code, _ = found
        prof_raw = json.loads(gophergrades_prof.invoke(code))
    return {"search": search_raw, "found": found, "prof": prof_raw}

# Profile endpoints
@app.get("/profile")
def get_profile_endpoint(user_id: str):
    profile = get_profile(user_id)
    return {"ok": True, "profile": profile}

@app.put("/profile")
def update_profile_endpoint(request: ProfileRequest):
    profile = save_profile(request.user_id, {
        "major": request.major,
        "level": request.level,
        "year": request.year,
        "personalization_notes": request.personalization_notes,
    })
    return {"ok": True, "profile": profile}

# GopherGrades testing as well as helpers for the agent to better identify when tools are needed
# This will also push for a better, more detailed response from the agent
@app.post("/umn/course")
def lookup_course(request: CourseLookupRequest):
    query = request.query.strip()

    try:
        search_result = json.loads(gophergrades_search.invoke(request.query))
        
        response = {
            "ok": True,
            "query": query,
            "search": search_result,
            "class": None
        }

        normalized = query.replace(" ", "").upper()

        if re.match(r"^[A-Z]{2,}\d{4}$", normalized):
            class_result = json.loads(gophergrades_class.invoke(normalized))
            response["class"] = class_result
        
        return response
    
    except Exception as e:
        return {
            "ok": False,
            "query": query,
            "error": str(e)
        }

@app.post("/umn/prof")
def lookup_professor(request: ProfessorLookupRequest):
    name = request.name.strip()

    try:
        search_result = json.loads(gophergrades_search.invoke(name))

        return {
            "ok": True,
            "name": name,
            "search": search_result
        }

    except Exception as e:
        return {
            "ok": False,
            "name": name,
            "error": str(e)
        }
    

@app.post("/umn/dept")
def lookup_department(request: DepartmentLookupRequest):
    dept = request.dept.strip().upper()

    try:
        raw_result = json.loads(gophergrades_dept.invoke(dept))

        if not raw_result.get("success") or not raw_result.get("data"):
            return {
                "ok": False,
                "dept": dept,
                "error": "Department not found."
            }

        data = raw_result["data"]
        normalized_courses = [
            _normalize_department_course(course)
            for course in data.get("distributions", [])
        ]

        return {
            "ok": True,
            "dept": {
                "campus": data.get("campus"),
                "code": data.get("dept_abbr"),
                "name": data.get("dept_name"),
            },
            "summary": _build_department_summary(normalized_courses),
            "featured": _build_department_featured(normalized_courses, data.get("dept_abbr")),
            "courses": normalized_courses,
        }

    except Exception as e:
        return {
            "ok": False,
            "dept": dept,
            "error": str(e)
        }
    

# Implementing History Permanent Storage 

# receives a conversation object from frontend, and store it
@app.post("/save")
def save_endpoint(request: ConversationRequest):
    
    # checks if json already exist, before saving.
    if os.path.exists(CONVERSATION_FILE):

        # exist, so read file
        with open(CONVERSATION_FILE, "r") as file:
            conversations = json.load(file)
    else:

        # doesn't exist, so make list to store temporarily
        conversations = []

    # find index of the existing conversation in list, if exist.
    match_index = next((i for i, c in enumerate(conversations) if c["id"] == request.id), None)

    # if conversation exist, overwrite it with updated version.
    if match_index is not None:
        # found index, loading message
        conversations[match_index] = {
            "id": request.id,
            "title": request.title,
            "messages": request.messages
        }
    else:
        # adds conversations components
        conversations.append({
            "id": request.id,
            "title": request.title,
            "messages": request.messages
        })

    # open file to write, creates if doesn't exist
    with open(CONVERSATION_FILE, "w") as file:
        json.dump(conversations, file, indent=2)

    # Good Return
    return {"ok": True}


# clears all saved conversations
@app.delete("/history/clear")
def clear_history_endpoint():
    if os.path.exists(CONVERSATION_FILE):
        os.remove(CONVERSATION_FILE)
    return {"ok": True}


# returns all saved conversations to the frontend
@app.get("/history")
def history_endpoint():
    # checks if file exist
    if os.path.exists(CONVERSATION_FILE):

        # opens and read file
        with open(CONVERSATION_FILE, "r") as file:

            # load file into parsed format
            conversations = json.load(file)

            # return file
            return {"ok": True, "conversations": list(reversed(conversations))}
    else:
        # file doesn't exist, return empty list
        return {"ok": True, "conversations": []}


def summarize_research_text(text, limit=200):
    if not text:
        return ""

    cleaned = re.sub(r"\s+", " ", str(text)).strip()
    cleaned = re.sub(r"(#{1,6}\s*)+", "", cleaned)

    if len(cleaned) <= limit:
        return cleaned

    shortened = cleaned[:limit].rsplit(" ", 1)[0].strip()
    return f"{shortened}..."
