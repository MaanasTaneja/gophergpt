from langchain_core.language_models import BaseChatModel
from langgraph.graph import START, END
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated

from autonomy.agent.base_agent import BaseStateAgent

class SimpleAgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]  # appended messages to the state...

class SimpleAgent(BaseStateAgent):
    def __init__(self, llm: BaseChatModel, system_prompt: str):
        super().__init__(SimpleAgentState)
        self.system_prompt = system_prompt
        self.runnable = llm

    def llm_node(self, state: SimpleAgentState, config: RunnableConfig = None):
        if config:
            response = self.runnable.invoke([self.system_prompt] + state["messages"], config)
        else:
            response = self.runnable.invoke([self.system_prompt] + state["messages"])
        return {"messages": [response]}

    def initworkflow(self):
        self.workflow.add_node("chat_node", self.llm_node)
        self.workflow.add_edge(START, "chat_node")
        self.workflow.add_edge("chat_node", END)
