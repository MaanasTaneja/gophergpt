import streamlit as st

from gophergpt.autonomy.agent.react_agent import ReActAgent
from gophergpt.autonomy.llm.openai_llm import OpenAILLM
from gophergpt.autonomy.tools.base import ToolkitManager 

from dotenv import load_dotenv
from langchain_tavily import TavilySearch
import os


# --- Define an Agent class ---
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
        return final_state["messages"][-1].content


# --- Initialize agent ---
if "agent" not in st.session_state:
    st.session_state.agent = ChatAgent()

if "messages" not in st.session_state:
    st.session_state.messages = []


# --- Streamlit Chat UI ---
st.title("💬 Chat with Agent")

# Display existing messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input box for user
if prompt := st.chat_input("Type your message..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get agent reply
    reply = st.session_state.agent.invoke(prompt)

    # Add agent reply
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)
