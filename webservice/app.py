from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from autonomy.agent.react_agent import ReActAgent
from autonomy.llm.openai_llm import OpenAILLM
from autonomy.tools.base import ToolkitManager 

from dotenv import load_dotenv
from langchain_tavily import TavilySearch
import os

from pydantic import BaseModel
from fastapi import APIRouter
from webservice.routers.research import router as research_router, run_research_query, ResearchRequest
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

class ChatRequest(BaseModel):

    message: str 

    # ensures loading the correct history and not all
    conversation_id: int | None = None # makes it optional, provide stability to frontend, since no history may exist

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

def extract_course_codes(text):
    """Extract normalized UMN course codes (e.g. CSCI4041) from a message."""
    pattern = r'\b([A-Z]{2,6})\s*(\d{4})\b'
    seen = []
    for m in re.finditer(pattern, text.upper()):
        code = f"{m.group(1)}{m.group(2)}"
        if code not in seen:
            seen.append(code)
    return seen


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


# responsible for loading/retrieving chat messages
@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    global gopher_assistant
    if gopher_assistant is None:
        return {"error": "Agent not initialized."}

    message = request.message.lower()

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
        query = request.message if re.search(r'rea?sea?rch', message) else build_research_query(message, history)
        research_data = run_research_query(ResearchRequest(query=query, max_results=5))
        summary_text = summarize_research_text(research_data.summary, limit=320)

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
                            "snippet": summarize_research_text(result.snippet, limit=190)
                        }
                        for result in research_data.results
                    ][:4]
                }
            ]
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
            ai_summary = gopher_assistant.invoke(guided_message, history=history)
            return {
                "response": "",
                "content": [{"type": "compare", "courses": courses, "summary": ai_summary}]
            }

    response = gopher_assistant.invoke(request.message, history=history)
    return {
        "response": response,
        "content": []
    }

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


def summarize_research_text(text, limit=200):
    if not text:
        return ""

    cleaned = re.sub(r"\s+", " ", str(text)).strip()
    cleaned = re.sub(r"(#{1,6}\s*)+", "", cleaned)

    if len(cleaned) <= limit:
        return cleaned

    shortened = cleaned[:limit].rsplit(" ", 1)[0].strip()
    return f"{shortened}..."
