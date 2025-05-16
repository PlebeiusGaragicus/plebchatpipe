"""This 'ollama' graph outlines a LangGraph agent with memory functionality."""


## DEFINE OUR GRAPH, ALONG WITH ITS SCHEMAS
from langgraph.graph import StateGraph, START, END


from graphs import configuration
from graphs.common import NodeOutputType

from graphs.fren.state import State

graph_builder = StateGraph(State, input=State, config_schema=configuration.Configuration)

## ADD ALL OUR NODES
from graphs.fren.nodes import init, check_for_command, handle_command, ollama
graph_builder.add_node("init", init)
graph_builder.add_node("ollama", ollama, metadata={"node_output_type": NodeOutputType.ANSWER})
graph_builder.add_node("handle_command", handle_command)


## CONNECT ALL OUR NODES
graph_builder.add_edge(START, "init")
graph_builder.add_conditional_edges("init", check_for_command)
graph_builder.add_edge("handle_command", END)
graph_builder.add_edge("ollama", END)

graph = graph_builder.compile()
