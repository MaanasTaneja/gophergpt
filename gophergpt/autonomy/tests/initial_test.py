from autonomy.agent.simple_agent import SimpleAgent
from autonomy.agent.react_agent import ReActAgent
from autonomy.agent.planning_exec_agent import PlanExecuteAgent
from autonomy.llm.openai_llm import OpenAILLM
from autonomy.tools.base import ToolkitManager 
from langchain_core.tools import tool

from langchain_tavily import TavilySearch
import os 
from dotenv import load_dotenv

load_dotenv()
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

llm = OpenAILLM(model_name="gpt-4o").get_model()
search_tool = TavilySearch(max_results = "5", topic = "general")

toolkit = ToolkitManager()

@tool
def hindi_greeting() -> str:
    """Returns a greeting in Hindi."""
    return "नमस्ते, आप कैसे हैं?"

@tool
def punjabi_greeting() -> str:
    """Returns a greeting in Hindi."""
    return "ਸਤ ਸ੍ਰੀ ਅਕਾਲ, ਤੁਸੀਂ ਕਿਵੇਂ ਹੋ?"

toolkit.register_tools([hindi_greeting, punjabi_greeting, search_tool], type="other")

react_agent = ReActAgent(llm=llm, toolkit=toolkit, system_prompt="You are a helpful assistant that can use tools to answer questions.")

#final_state = react_agent.invoke_agent({"messages": [{"role": "user", "content": "where is durgapur located search on google"}]})
#print(final_state["messages"][-1].content)


plan_execute_agent = PlanExecuteAgent(llm, toolkit=toolkit, react_agent_prompt= "You are a helpful tool executor assistant, run and solve the task given to you.")
plan_final_state = plan_execute_agent.invoke_agent({"input": "where is durgapur located search on google"})
print(plan_final_state["messages"][-1].content)