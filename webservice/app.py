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

class ChatRequest(BaseModel):
    message: str

class ChatAgent:
    def __init__(self, name="Assistant"):
        self.name = name

        load_dotenv()
        os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

        self.llm = OpenAILLM(model_name="gpt-4o").get_model()
        search_tool = TavilySearch(max_results = "5", topic = "general", include_domains=["umn.edu"])

        self.toolkit = ToolkitManager()

        self.toolkit.register_tools([search_tool], type="other")
        self.react_agent = ReActAgent(llm=self.llm, toolkit=self.toolkit, system_prompt="You are a helpful assistant that can use tools to answer questions.")

    def invoke(self, message: str) -> str:
        """
        Replace this method with your LLM/agent logic.
        For now, it just echoes back the message.
        """
        final_state = self.react_agent.invoke_agent({"messages": [{"role": "user", "content": message}]})
        generation = final_state["messages"][-1].content
        return generation


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


#this is epheremel, we need to store the chat history in the frtonend, but we will do this later.
@app.post("/chat") 
def chat_endpoint(request: ChatRequest):
    global gopher_assistant
    if gopher_assistant is None:
        return {"error": "Agent not initialized."}
    response = gopher_assistant.invoke(request.message)
    return {"response": response}
