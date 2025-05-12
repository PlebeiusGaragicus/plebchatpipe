"""This is an example LangGraph agent with the most basic functionality."""


##############################################################
### DEFINE GRAPH STATE
##############################################################
import operator
from typing import Annotated
from pydantic import BaseModel, Field


class State(BaseModel):
    messages: Annotated[list, operator.add] = Field(default_factory=list)


##############################################################
### DEFINE GRAPH NODES
##############################################################
from langchain_core.runnables import RunnableConfig
from langgraph.types import StreamWriter

from graphs import configuration
from graphs.common import NodeOutputType, think, answer, think_codeblock


def echo(state: State, config: RunnableConfig, writer: StreamWriter):
    configurable = configuration.Configuration.from_runnable_config(config)
    print(configurable)
    print(configurable)
    print(configurable)
    print(configurable)
    
    # Display debug information if DEBUG is True
    if configurable.DEBUG == True:
        # # Display all configuration attributes as a code block
        think_codeblock(configurable.__dict__, writer=writer)
        
        # Access dynamically added attributes
        if hasattr(configurable, 'thread_id'):
            think(f"Thread ID: {configurable.thread_id}", writer=writer)
            
        # Show some attitude in debug mode
        think("Geesh... this guy's an idiot amirite?", writer=writer)

    # Echo back the user's message
    echoback = state.messages[-1]['content']
    answer(echoback, writer=writer)


##############################################################
### BUILD THE GRAPH
##############################################################
from langgraph.graph import StateGraph, START, END


graph_builder = StateGraph(State, input=State, config_schema=configuration.Configuration)

graph_builder.add_node("echo", echo, metadata={"node_output_type": NodeOutputType.ANSWER})
graph_builder.add_edge(START, "echo")
graph_builder.add_edge("echo", END)

graph = graph_builder.compile()