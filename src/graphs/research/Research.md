# Research Agent Design Documentation

## Overview

The Research Agent is a LangGraph-based agent that provides web search and research capabilities within the PlebChat application. It follows the convention of the "fren" graph structure while implementing specialized functionality for web search and comprehensive answer generation.

## Architecture

The Research Agent is structured as a LangGraph with the following components:

### 1. State Management (`state.py`)

The state model defines the data structure that flows through the graph:

```python
class State(BaseModel):
    query: Optional[str] = None
    messages: Annotated[list, operator.add] = Field(default_factory=list)
    search_results: List[Dict[str, Any]] = Field(default_factory=list)
    answer: Optional[str] = Field(default=None)
    error: Optional[str] = Field(default=None)
    focus_mode: str = Field(default="all")
    conversation_id: Optional[int] = Field(default=None)
    conversation_history: Optional[List[Dict[str, str]]] = Field(default=None)
```

Key state components:
- `query`: The user's search query
- `messages`: Conversation history in a format compatible with LLM chat models
- `search_results`: Results from web searches
- `answer`: The final answer to return to the user
- `error`: Error message if any

- `conversation_id` and `conversation_history`: For handling follow-up questions

### 2. Nodes (`nodes.py`)

The nodes represent the individual processing steps in the research workflow:

#### `search_web` Node
- Performs web searches using SearXNG
- Formats and processes search results
- Outputs search results as "thoughts" using StreamWriter
- Updates the state with search results

#### `generate_answer` Node
- Analyzes search results
- Generates comprehensive answers with citations
- Outputs analysis process as "thoughts" using StreamWriter
- Provides streaming response capability

#### `ollama` Node
- Fallback node for direct interaction without search
- Handles simple queries that don't require web search
- Maintains conversation context

### 3. Graph Definition (`graph.py`)

The graph defines the workflow and routing logic:

```python
graph_builder.add_node("search_web", search_web, metadata={"node_output_type": "thought"})
graph_builder.add_node("generate_answer", generate_answer, metadata={"node_output_type": "answer"})
graph_builder.add_node("ollama", ollama, metadata={"node_output_type": "answer"})

graph_builder.add_conditional_edges("__start__", _should_search)
graph_builder.add_edge("search_web", "generate_answer")
graph_builder.add_edge("generate_answer", "__end__")
graph_builder.add_edge("ollama", "__end__")
```

#### Conditional Routing
The `_should_search` function determines whether to perform a web search or use the LLM directly:
- If search results already exist, proceed to answer generation
- If the query contains research-related keywords, perform a web search
- Otherwise, use the LLM directly for simple queries

## Integration with SearXNG

The Research Agent integrates with SearXNG for web search capabilities:

1. **Configuration**: SearXNG URL is configured in the `Config` class
2. **Docker Integration**: SearXNG is included in the docker-compose.yaml file
3. **Search Implementation**: The `perform_web_search` function in `nodes.py` handles the API calls to SearXNG

```python
def perform_web_search(query: str, searxng_url: str) -> tuple:
    """Perform a web search using SearXNG."""
    # Implementation details...
```

## User Experience

From the user's perspective, the Research Agent provides:

1. **Intelligent Query Handling**: Automatically determines whether a query requires web search
2. **Transparent Process**: Shows search results and analysis as "thoughts" in the UI
3. **Comprehensive Answers**: Generates detailed responses based on search results
4. **Source Citations**: Includes citations to sources using the format [1], [2], etc.
5. **Streaming Responses**: Provides real-time streaming of responses
6. **Error Handling**: Gracefully handles errors in search or answer generation

## System Prompts

The Research Agent uses a specialized system prompt to guide its behavior:

```
You are a helpful research assistant that provides comprehensive answers based on web search results.

Your goal is to:
1. Analyze search results thoroughly
2. Provide accurate, well-structured responses
3. Include relevant citations to sources using the format [1], [2], etc.
4. Be objective and factual in your analysis

Always base your answers solely on the provided search results. If the search results don't contain enough information to answer the question, say so clearly.
```

## Technical Implementation Details

### Search Process

1. The user query is sent to SearXNG with appropriate parameters
2. Search results are processed and formatted
3. The LLM is prompted with the search results and query
4. The LLM generates a comprehensive answer with citations
5. The response is streamed back to the user

### Error Handling

The Research Agent includes robust error handling:
- Search errors are caught and reported to the user
- LLM generation errors are handled gracefully
- Fallback mechanisms ensure the user always gets a response

### Integration with PlebChat

The Research Agent is integrated with the PlebChat application:
- Registered in the graph registry as "research"
- Accessible via the UI with the name "🔍 Research"
- Compatible with the existing streaming API

## Future Enhancements

Potential future enhancements for the Research Agent:

1. **Advanced Search Filtering**: Implement more sophisticated search filtering options
2. **Multi-Source Research**: Integrate with additional data sources beyond web search
3. **Fact-Checking**: Add verification mechanisms for search results
4. **Personalized Research**: Adapt search and answer generation based on user preferences
5. **Citation Management**: Improve citation formatting and management

## Conclusion

The Research Agent provides a powerful web research capability within the PlebChat application, following the established LangGraph architecture while implementing specialized functionality for search and answer generation. It demonstrates the flexibility of the LangGraph framework for creating specialized agents with different capabilities.
