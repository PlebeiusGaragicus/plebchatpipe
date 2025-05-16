"""This 'ollama' graph outlines a LangGraph agent with memory functionality."""


## DEFINE OUR GRAPH, ALONG WITH ITS SCHEMAS
from langgraph.graph.state import StateGraph

from ..config import Config
from ..common import NodeOutputType
from .state import State
graph_builder = StateGraph(State, input=State, config_schema=Config)


## ADD ALL OUR NODES
from .nodes import ollama, _check_for_command, handle_command
graph_builder.add_node("ollama", ollama, metadata={"node_output_type": NodeOutputType.ANSWER})
graph_builder.add_node("handle_command", handle_command)


## CONNECT ALL OUR NODES
graph_builder.add_conditional_edges("__start__", _check_for_command)
graph_builder.add_edge("handle_command", "__end__")
graph_builder.add_edge("ollama", "__end__")

graph = graph_builder.compile()
