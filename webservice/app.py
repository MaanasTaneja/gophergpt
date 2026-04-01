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
from webservice.routers.research import router as research_router
import json
import re

from typing import Optional

from webservice.profile_store import (
    init_store,
    get_profile,
    save_profile,
    save_conversation,
    get_conversations,
)
from webservice.personalization import build_personalized_prompt

from autonomy.tools.gophergrades_api import gophergrades_search, gophergrades_class, gophergrades_prof, gophergrades_dept

# GopherGrades Testing Endpoint
class CourseLookupRequest(BaseModel):
    query: str

class ProfessorLookupRequest(BaseModel):
    name: str

class ChatRequest(BaseModel):
    user_id: str
    message: str

class ProfileRequest(BaseModel):
    user_id: str
    major: str
    year: str
    personalization_notes: str = ""

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

    def invoke(self, message: str, profile: Optional[dict]) -> str:
        """
        Replace this method with your LLM/agent logic.
        For now, it just echoes back the message.
        """
        personalized_context = build_personalized_prompt(profile or {})
        full_message = message

        if personalized_context:
            full_message = f"{personalized_context}\n\nUser message:\n{message}"

        final_state = self.react_agent.invoke_agent({"messages": [{"role": "user", "content": full_message}]})
        generation = final_state["messages"][-1].content
        return generation
    

# History Classes

class ConversationRequest(BaseModel):
    user_id: str
    id: int
    title: str
    messages: list


gopher_assistant  = None

@asynccontextmanager
async def lifespan_function(app : FastAPI):
    global gopher_assistant 
    init_store()
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


#this is epheremel, we need to store the chat history in the frtonend, but we will do this later.
@app.post("/chat") 
def chat_endpoint(request: ChatRequest):
    global gopher_assistant
    if gopher_assistant is None:
        return {"error": "Agent not initialized."}
    
    profile = get_profile(request.user_id)
    response = gopher_assistant.invoke(request.message, profile=profile)
    return {"response": response}

@app.get("/profile")
def get_profile_endpoint(user_id: str):
    profile = get_profile(user_id)
    return {"ok": True, "profile": profile}

@app.put("/profile")
def update_profile_endpoint(request: ProfileRequest):
    profile = save_profile(
        request.user_id,
        {
            "major": request.major,
            "year": request.year,
            "personalization_notes": request.personalization_notes,
        }
    )
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
    

# Implementing History Permanent Storage 

# receives a conversation object from frontend, and store it
@app.post("/save")
def save_endpoint(request: ConversationRequest):
    # checks if json already exist, before saving.
    save_conversation(
        user_id=request.user_id,
        conversation_id=request.id,
        title=request.title,
        messages=request.messages,
    )
    return {"ok": True}

# returns all saved conversations to the frontend
@app.get("/history")
def history_endpoint(user_id: str):
    conversations = get_conversations(user_id)
    return {"ok": True, "conversations": conversations}
