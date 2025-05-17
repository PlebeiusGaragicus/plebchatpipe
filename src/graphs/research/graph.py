"""
This research graph outlines a LangGraph agent for web research.

"""

import operator
from typing import Optional, Annotated, List, Dict, Any
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, START, END
from langgraph.types import StreamWriter
from langchain_core.runnables import RunnableConfig
from langchain_ollama import ChatOllama

from graphs import configuration
from graphs.commands import CommandHandler
from graphs.common import NodeOutputType, answer, think, think_codeblock




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
        think(f">> I found a command! `{query}`", writer=writer)
        think( '\n---\n', writer=writer )
        return "handle_command"

    think(">> no command... continue", writer=writer)
    think( '\n---\n', writer=writer )
    return "router"


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

    # Get command output
    cmd_output = CommandHandler._run(command, arguments)

    # Handle the command output based on its properties
    if cmd_output.returnDirect:
        # Return the output directly to the user
        answer(cmd_output.cmdOutput, writer=writer)
        return

    else:
        # The output should be processed by an LLM before returning to the user
        think(f"Processing command output with LLM...", writer=writer)
        think( '---', writer=writer )
        think( "### command output:", writer=writer )
        think( cmd_output.cmdOutput, writer=writer )
        think( '---', writer=writer )


        # Create prompt for LLM
        prompt = cmd_output.reinjectionPrompt or "Process this information and provide a helpful response:"

        # Get the LLM

        # Prepare messages for the LLM
        messages = [
            {"role": "system", "content": cmd_output.reinjectionPrompt},
            {"role": "user", "content": f"{prompt}\n\n{cmd_output.cmdOutput}"}
        ]

        llm = get_llm(config)
        response = llm.stream(messages)

        # Join all chunks into a single response
        full_response = "".join(chunk.content for chunk in response)

        # Add the assistant's response to the message history
        assistant_message = {"role": "assistant", "content": full_response}
        state.messages.append(assistant_message)

        # Return the updated messages list with the new response
        return {"messages": [assistant_message]}



############################################################################
# NODE
############################################################################
def router(state: State, config: RunnableConfig, writer: StreamWriter):

    think("nothing", writer=writer)


    # check if the last message was from the 'assistant' - if so, this convo was continued.  If not, this convo is NEW
    if state.messages[-1].get("role", None) == 'assistant':
        answer("NEW CONVO DETECTED", writer=writer)
        return "search"
    else:
        answer("CONVO IS BEING CONTINUED", writer=writer)






graph_builder = StateGraph(State, input=State, config_schema=configuration.Configuration)

graph_builder.add_conditional_edges(START, _check_for_command)
# We route to either of these...
graph_builder.add_node("handle_command", handle_command)
graph_builder.add_node("router", router, metadata={"node_output_type": NodeOutputType.THOUGHT})



# __end__
graph_builder.add_edge("handle_command", END)
graph_builder.add_edge("router", END)

graph = graph_builder.compile()
