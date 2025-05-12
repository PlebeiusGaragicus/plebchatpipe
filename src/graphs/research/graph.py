"""This research graph outlines a LangGraph agent for web research."""


import operator
from typing import Optional, Annotated, List, Dict, Any
from pydantic import BaseModel, Field



import json
import logging
from typing import Dict, Any, List, Optional

from langchain_core.runnables import RunnableConfig
from langchain_ollama import ChatOllama
from langgraph.graph.state import StateGraph
from langgraph.types import StreamWriter

from ..config import Config
from ..common import write_content, write_thoughts

from .commands import CommandHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


############################################################################
# PROMPTS
############################################################################
SYSTEM_PROMPT = """You are a helpful research assistant that provides comprehensive answers based on web search results.

Your goal is to:
1. Analyze search results thoroughly
2. Provide accurate, well-structured responses
3. Include relevant citations to sources using the format [1], [2], etc.
4. Be objective and factual in your analysis

Always base your answers solely on the provided search results. If the search results don't contain enough information to answer the question, say so clearly.
"""


############################################################################
# STATE
############################################################################
class State(BaseModel):
    """State for the research agent graph."""
    query: Optional[str] = None
    messages: Annotated[list, operator.add] = Field(default_factory=list)

    search_results: List[Dict[str, Any]] = Field(default_factory=list, description="Results from search engine")
    answer: Optional[str] = Field(default=None, description="The final answer to return to the user")
    error: Optional[str] = Field(default=None, description="Error message if any")


############################################################################
# HELPER FUNCTIONS
############################################################################
def get_llm(config: RunnableConfig):
    """Get the LLM model based on the configuration."""
    configurable = Config.from_runnable_config(config)
    
    return ChatOllama(
        model=configurable.LLM_MODEL,
        keep_alive=configurable.KEEP_ALIVE,
        base_url=configurable.OLLAMA_BASE_URL
    )


############################################################################
# CONDITIONAL NODE
############################################################################
def _check_for_command(state: State, config: RunnableConfig, writer: StreamWriter):
    """
        NOTE: This is the first conditional node on our graph
        It checks if the last message (aka user query) starts with a '/'.
        This function is prefixed with a '_' so that it's progress doesn't show in the frontend UI
    """

    #TODO: check state query
    query = state.messages[-1]['content']
    # print(query)

    if query.startswith("/"):
        writer( write_thoughts(f"I found a command! `{query}`") )
        return "handle_command"

    writer( write_thoughts("no command... continue") )
    return "ollama"


############################################################################
# NODE
############################################################################
def handle_command(state: State, config: RunnableConfig, writer: StreamWriter):
    # extract command
    query = state.messages[-1]['content']
    split = query.split(" ")

    # Remove the slash and take the first word
    command = split[0][1:].lower()
    arguments = split[1:]

    if not command:
        command = ""

    response = CommandHandler._run(command, arguments)
    #NOTE: This node doesn't have an LLM call, but we can output a reply this way
    writer( write_content( response ) )


############################################################################
# NODE
############################################################################
def ollama(state: State, config: RunnableConfig, writer: StreamWriter):

    # If we have a new user query, add it to the messages
    if state.query:
        # Add the user's query to the message history
        user_message = {"role": "user", "content": state.query}
        # Ensure we're not duplicating the message if it's already in the state
        if not state.messages or state.messages[-1] != user_message:
            state.messages.append(user_message)

    # Add system prompt to messages if it's not already there
    # Check if the first message is a system message
    if not state.messages or state.messages[0].get("role") != "system":
        # Prepend system prompt to messages
        state.messages = [{"role": "system", "content": SYSTEM_PROMPT}] + state.messages



    print("*"*30)
    print("GRAPH STATE INSIDE THE NODE")
    for m in state.messages:
        print(json.dumps(m, indent=2))
    print("*"*30)

    # writer( write_thoughts() )
    writer( write_content("nothing") )

    # KEEP ALL THIS
    # # Call the LLM with the full conversation history
    # llm = get_llm(config)
    # response = llm.stream(state.messages)

    # # Join all chunks into a single response
    # full_response = "".join(chunk.content for chunk in response)

    # # Add the assistant's response to the message history
    # assistant_message = {"role": "assistant", "content": full_response}
    # state.messages.append(assistant_message)

    # print('='*40)
    # print("THE ASSISTANT SAID..")
    # print(assistant_message)
    # print('='*40)

    # # Return the updated messages list with the new response
    # return {"messages": [assistant_message]}






from ..config import Config
graph_builder = StateGraph(State, input=State, config_schema=Config)


## ADD ALL OUR NODES
graph_builder.add_node("ollama", ollama, metadata={"node_output_type": "answer"})
graph_builder.add_node("handle_command", handle_command)


## CONNECT ALL OUR NODES
graph_builder.add_conditional_edges("__start__", _check_for_command)
graph_builder.add_edge("handle_command", "__end__")
graph_builder.add_edge("ollama", "__end__")

graph = graph_builder.compile()
