import os
import json
from typing import TypedDict
from langchain.tools import tool
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage

class ToolkitManager:
    def __init__(self):
        self.tool_reference = {}  # A flat mapping of all tools by name to function.
        self.toolkit = { "retriever": [], "analysis": [], "other": [] }

    def _enrich_tool_docstring(self, tool, type: str):
        if not tool.__doc__:
            raise ValueError("Tool must have a docstring.")

        if type == "retriever":
            tool.__doc__ = "Type: Retriever Tool, this tool is used to retrieve data from AWS, useful for enriching investigation context and provide more data to analyst.\\n\\n" + tool.__doc__
        elif type == "analysis":
            tool.__doc__ = "Type: Analysis Tool, this tool is used to analyze the data received from AWS, useful for making inferences and figuring out what is wrong.\\n\\n" + tool.__doc__
        else:
            tool.__doc__ = "Type: Other Tool, this tool is general purpose and can be used in any context.\\n\\n" + tool.__doc__
        return tool

    def register_tool(self, tool, type: str = "other"):
        '''Register a tool with the toolkit manager. type can be 'retriever', 'analysis', or 'other'.'''
        if type not in self.toolkit:
            raise ValueError("Invalid tool type: {}. Type must be one of 'retriever', 'analysis', or 'other'.".format(type))
        if tool.name in self.tool_reference:
            raise ValueError("Tool with name {} is already registered.".format(tool.name))

        #self._enrich_tool_docstring(tool, type)
        self.tool_reference[tool.name.lower()] = tool
        self.toolkit[type].append(tool)

    def register_tools(self, tools, type: str = "other"):
        '''Register multiple tools with the toolkit manager.'''
        for tool in tools:
            self.register_tool(tool, type)

    def get_all_tools(self):
        '''Get all tools registered in the toolkit manager.'''
        return list(self.tool_reference.values())

    def get_retriever_tools(self):
        return self.toolkit.get("retriever", [])

    def get_analysis_tools(self):
        return self.toolkit.get("analysis", [])

    def get_tools_reference(self):
        '''Get a flat mapping of all tools by name to function.'''
        return self.tool_reference
    
    def get_toolkit_description(self):
        description = "Toolkit contains the following tools:\\n\\n"
        for name, tool in self.tool_reference.items():
            description += f"{name}: {tool.description}\\n\\n"
        return description

    def get_tool_by_name(self, name: str):
        '''Get a tool by its name.'''
        if name in self.tool_reference:
            return self.tool_reference[name]
        else:
            raise ValueError("Tool with name {} not found.".format(name))
