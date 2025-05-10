"""This 'ollama' graph outlines a LangGraph agent with memory functionality."""

from langgraph.graph.state import StateGraph

## DEFINE OUR GRAPH, ALONG WITH ITS SCHEMAS
from .state import State, Result, Config
graph_builder = StateGraph(State, input=State, output=Result, config_schema=Config)


## ADD ALL OUR NODES
from .nodes import ollama, _check_for_command, handle_command, nothing, thick, thought_llama
graph_builder.add_node("thick", thick, metadata={"node_output_type": "thought"})
graph_builder.add_node("thought_llama", thought_llama, metadata={"node_output_type": "thought"})
graph_builder.add_node("ollama", ollama, metadata={"node_output_type": "answer"})
graph_builder.add_node("nothing", nothing)
graph_builder.add_node("handle_command", handle_command)


## CONNECT ALL OUR NODES
graph_builder.add_conditional_edges("__start__", _check_for_command)
graph_builder.add_edge("handle_command", "__end__")


graph_builder.add_edge("thick", "thought_llama")
graph_builder.add_edge("thought_llama", "ollama")
graph_builder.add_edge("ollama", "nothing")
graph_builder.add_edge("nothing", "__end__")

# graph_builder.add_edge("ollama", "__end__")

graph = graph_builder.compile()
