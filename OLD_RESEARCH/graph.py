"""This research graph outlines a LangGraph agent for web search and research."""

## DEFINE OUR GRAPH, ALONG WITH ITS SCHEMAS
from langgraph.graph.state import StateGraph

from ..config import Config
from .state import State
graph_builder = StateGraph(State, input=State, config_schema=Config)


## ADD ALL OUR NODES
from .nodes import search_web, generate_answer, ollama
graph_builder.add_node("search_web", search_web, metadata={"node_output_type": "thought"})
graph_builder.add_node("generate_answer", generate_answer, metadata={"node_output_type": "answer"})
graph_builder.add_node("ollama", ollama, metadata={"node_output_type": "answer"})


## DEFINE CONDITIONAL ROUTING
def _should_search(state: State):
    """
    Determine if we should perform a web search or just use the LLM.
    This function is prefixed with a '_' so that it doesn't show in the frontend UI.
    """
    # If we already have search results, we don't need to search again
    if state.search_results:
        return "generate_answer"
    
    # Get the query
    query = state.query or (state.messages[-1]['content'] if state.messages else "")
    
    # Check for very simple queries that don't need a search
    simple_queries = [
        "hello", "hi", "hey", "test", "thanks", "thank you"
    ]
    
    if query.lower().strip() in simple_queries:
        return "ollama"
    
    # For all other queries, perform a web search by default
    return "search_web"


## CONNECT ALL OUR NODES
graph_builder.add_conditional_edges("__start__", _should_search)
graph_builder.add_edge("search_web", "generate_answer")
graph_builder.add_edge("generate_answer", "__end__")
graph_builder.add_edge("ollama", "__end__")

graph = graph_builder.compile()
