from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from typing import TypedDict, Annotated, List, Union
from pydantic import BaseModel, Field
import operator

from autonomy.agent.base_agent import BaseStateAgent
from autonomy.agent.react_agent import ReActAgent
from autonomy.tools.base import ToolkitManager
from autonomy.prompts import (
    plan_execute_replanner_prompt,
    plan_execute_planner_prompt,
    plan_execute_react_agent_prompt,
    plan_execute_rephraser_prompt,
)

class Plan(BaseModel):
    steps: List[str] = Field(description="List of steps to be executed in the plan.")

class Response(BaseModel):
    content: str = Field(description="Response to be returned to the user")

class Feedback(BaseModel):
    action: Union[Plan, Response] = Field(description="Action taken by the agent, can be a list of actions or if nothing else to do we can return to user, plan is done.")

class PlanExecuteAgentState(TypedDict):
    input: str
    past_steps: Annotated[List[tuple], operator.add]  # unlike other chatbot states, we only need to store past steps generated..
    plan: List[str]
    response: str

class PlanExecuteAgent(BaseStateAgent):
    def __init__(self, llm: BaseChatModel, toolkit: ToolkitManager, planner_prompt: str = plan_execute_planner_prompt,
                 replanner_prompt: str = plan_execute_replanner_prompt, react_agent_prompt: str = plan_execute_react_agent_prompt):
        super().__init__(PlanExecuteAgentState)
        self.toolkit = toolkit
        self.llm = llm
        self.runnable = llm

        self.react_agent = ReActAgent(self.runnable, self.toolkit, react_agent_prompt)

        self.planner_prompt = ChatPromptTemplate.from_messages([("system", planner_prompt)])
        self.planning_agent = self.runnable.with_structured_output(Plan)

        self.replanner_prompt = ChatPromptTemplate.from_messages([("system", replanner_prompt)])
        self.replanner_agent = self.runnable.with_structured_output(Feedback)

        self.rephrase_prompt = ChatPromptTemplate.from_messages([("system", plan_execute_rephraser_prompt)])
        self.rephraser_agent = self.runnable.with_structured_output(Response)

    def execute_step(self, state: PlanExecuteAgentState):
        plan = state["plan"]
        objective = state["input"]

        plan_str = "\n".join([f"{i+1}. {step}" for i, step in enumerate(plan)])
        task = plan[0]  # always only execute first step

        task_formatted = f"The following objective/input \\n\\n {objective} \\n\\n and the following plan to complete the objective:\\n\\n{plan_str}\\n\\n You are tasked with executing step (1), {task}."
        agent_response = self.react_agent.execute({
            "messages": [{"role": "user", "content": task_formatted}]
        })

        return {
            "past_steps": [(task, agent_response)],
        }
    
    def plan_step(self, state : PlanExecuteAgentState):
        plan_generated = self.planning_agent.invoke({"input" : state["input"], "tools":  self.toolkit.get_toolkit_description()})
        return {"plan" : plan_generated.steps} #list shoudl go to state not the pydantic model.

    def replan_step(self, state: PlanExecuteAgentState):
        output = self.replanner_agent.invoke({
            "input": state["input"],
            "plan": state["plan"],
            "past_steps": state["past_steps"],
            "tools": self.toolkit.get_toolkit_description()
        })
        if isinstance(output.action, Response):
            return {"response": output.action.content}
        else:
            return {"plan": output.action.steps}

    def rephrase_step(self, state: PlanExecuteAgentState):
        rephrased_response = self.rephraser_agent.invoke({
            "past_steps": state["past_steps"],
            "response": state["response"]
        })
        return {"response": rephrased_response.content}

    def should_end(self, state: PlanExecuteAgentState):
        if "response" in state and state["response"]:
            return "rephraser"
        else:
            return "executor"

    def initworkflow(self):
        self.workflow.add_node("planner", self.plan_step)
        self.workflow.add_node("executor", self.execute_step)
        self.workflow.add_node("replanner", self.replan_step)
        self.workflow.add_node("rephraser", self.rephrase_step)

        self.workflow.add_edge(START, "planner")
        self.workflow.add_edge("planner", "executor")
        self.workflow.add_edge("executor", "replanner")
        self.workflow.add_conditional_edges("replanner", self.should_end, {
            "rephraser" : "rephraser",
            "executor" : "executor"
        })
        self.workflow.add_edge("rephraser", END)  # end the graph after rephraser

    def execute(self, messages) -> dict:
        graph_output = super().invoke_agent(messages)
        return graph_output["response"]
