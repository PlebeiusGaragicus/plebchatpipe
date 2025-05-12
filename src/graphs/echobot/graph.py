"""
This is an example LangGraph agent with the most basic functionality.

It serves as an example.

"""

#TODO: graph.get_graph().draw_mermaid_png())



##############################################################
### DEFINE GRAPH STATE
##############################################################
import os
import operator
from pydantic import BaseModel, Field
from typing import Optional, Any, Annotated

from langchain_core.runnables import RunnableConfig


##############################################################
class State(BaseModel):
    messages: Annotated[list, operator.add] = Field(default_factory=list)







##############################################################
### DEFINE OUR NODES
##############################################################
from langgraph.types import StreamWriter

# These are my custom enhancements
from ..common import write_content, write_thought, NodeOutputType
from graphs import configuration

##############################################################
#NOTE: since we aren't using an LLM to generate tokens, we need to use the writer to print to the UI
def echo(state: State, config: RunnableConfig, writer: StreamWriter):

    # Get the `DEBUG` setting from the config
    configurable = configuration.Configuration.from_runnable_config(config)

    print("*"*40)
    print(configurable)
    print(configurable.DEBUG)

    if configurable.DEBUG == True:
        writer( write_thought( "Geesh... this guy's an idiot amirite?" ) )

    echoback = state.messages[-1]['content']
    writer( write_content( echoback ) )



##############################################################
### BUILD THE GRAPH
##############################################################
from langgraph.graph import StateGraph, START, END


##############################################################
graph_builder = StateGraph(State, input=State, config_schema=configuration.Configuration)

graph_builder.add_node("echo", echo, metadata={"node_output_type": NodeOutputType.ANSWER})
graph_builder.add_edge(START, "echo")
graph_builder.add_edge("echo", END)

graph = graph_builder.compile()
