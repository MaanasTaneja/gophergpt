from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from autonomy.agent.react_agent import ReActAgent
from autonomy.llm.openai_llm import OpenAILLM
from autonomy.tools.base import ToolkitManager 

from dotenv import load_dotenv
from langchain_tavily import TavilySearch
import os
import statistics

from pydantic import BaseModel
from fastapi import APIRouter
from webservice.routers.research import router as research_router
import json
import re

from autonomy.tools.gophergrades_api import gophergrades_search, gophergrades_class, gophergrades_prof, gophergrades_dept


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


def _build_department_featured(courses):
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

    challenging_pool = [
        course
        for course in courses
        if course["metrics"]["challenge_rate"] is not None
        and _sum_grade_counts(course.get("grades")) >= 100
    ]
    most_challenging = sorted(
        challenging_pool,
        key=lambda course: (
            course["metrics"]["challenge_rate"],
            course.get("total_students", 0),
        ),
        reverse=True,
    )[:8]

    return {
        "popular": popular,
        "best_rated": best_rated,
        "most_challenging": most_challenging,
    }

class ChatAgent:
    def __init__(self, name="Assistant"):
        self.name = name

        load_dotenv()
        os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

        self.llm = OpenAILLM(model_name="gpt-4o").get_model()
        search_tool = TavilySearch(max_results = "5", topic = "general", include_domains=["umn.edu"])

        self.toolkit = ToolkitManager()

        self.toolkit.register_tools([search_tool], type="other")

        # Adding gopherGrade tools to agent
        gopherGradeTools = [gophergrades_search, gophergrades_class, gophergrades_prof, gophergrades_dept]
        self.toolkit.register_tools(gopherGradeTools, type="retriever")

        # Giving the agent a base system prompt to give some guidence in its role
        self.react_agent = ReActAgent(llm=self.llm, toolkit=self.toolkit, 
                                      system_prompt=(
                                          "You are a helpful assistant for University of Minnesota students. "
                                          "When a user asks about UMN courses, professors, grade distributions, GPA trends, "
                                          "or departments, use the GopherGrades tools to retrieve accurate information. "
                                          "Prefer tool-based answers over guessing. "
                                          "If a professor name is ambiguous, use search first before using a professor tool."
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

        # prepends all prior messages to pass into agent
        messages = history + [{"role": "user", "content": message}]

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
async def lifespan_function(app : FastAPI):
    global gopher_assistant 
    gopher_assistant = ChatAgent()
    yield

app = FastAPI(lifespan=lifespan_function)
app.include_router(research_router)
app.add_middleware(CORSMiddleware, 
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "The greatest openai wrapper ever made."}

# responsible for loading/retrieving chat messages
@app.post("/chat") 
def chat_endpoint(request: ChatRequest):
    global gopher_assistant
    if gopher_assistant is None:
        return {"error": "Agent not initialized."}
    

    """
    Loads the conversation history from file "app/data"
    """

    # empty history, append each if exist, else pass empty (default)
    history = []

    # only load history if we have an ID to lookup (from frontend) and file that exist
    if request.conversation_id is not None and os.path.exists(CONVERSATION_FILE):

        # open and read/parse conversations from file into memory
        with open(CONVERSATION_FILE, "r") as file:
            conversations = json.load(file)

        # find the correct matching conversation_id to return
        match = next((c for c in conversations if c["id"] == request.conversation_id), None)

        # if found extract the role and contents from stored messages in format for agent
        if match:
            history = [{
                "role": "user" if msg["isUser"] else "assistant", 
                "content": msg["text"]}
                for msg in match["messages"]
            ]

        
    # pass history back into agent
    response = gopher_assistant.invoke(request.message, history=history)
    return {"response": response}

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
            "featured": _build_department_featured(normalized_courses),
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
