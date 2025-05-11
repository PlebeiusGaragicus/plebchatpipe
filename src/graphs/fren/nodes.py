import json

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

from langgraph.types import StreamWriter

from ..config import Config
from .state import State, SYSTEM_PROMPT
from .commands import CommandHandler

# from ..common import OLLAMA_HOST

############################################################################
# HELPER FUNCTIONS
############################################################################
def get_llm(config: RunnableConfig):
    configurable = Config.from_runnable_config(config)

    print("@#$"*15)
    print(configurable)
    return ChatOllama(
        model=configurable.LLM_MODEL,
        keep_alive=configurable.KEEP_ALIVE,
        base_url=configurable.OLLAMA_BASE_URL
    )


############################################################################
# CONDITIONAL NODE
############################################################################
def _check_for_command(state: State, config: RunnableConfig):
    """
        NOTE: This is the first conditional node on our graph
        It checks if the last message (aka user query) starts with a '/'.
        This function is prefixed with a '_' so that it's progress doesn't show in the frontend UI
    """
    query = state.messages[-1]['content']
    # print(query)
    if query.startswith("/"):
        return "handle_command"
    return "ollama"

from ..common import write_content

############################################################################
# NODE
############################################################################
def handle_command(state: State, config: RunnableConfig, writer: StreamWriter):
    # configurable = Config.from_runnable_config(config)

    # extract command
    query = state.messages[-1]['content']
    split = query.split(" ")
    # Remove the slash and take the first word
    command = split[0][1:].lower()
    arguments = split[1:]

    print("%"*20)
    print(f"DEBUG: {command}, {arguments}")

    # check if command is empty
    if not command:
        command = ""
        # return {"messages": [{"role": "assistant", "content": "⚠️ Please provide a command.\n\n**Example:**\n```\n/help\n```"}]}
    

    # Use CommandHandler class method directly
    response = CommandHandler._run(command, arguments)

    writer( write_content( response ) )

    # return {"messages": [{"role": "assistant", "content": response}]}



############################################################################
# NODE
############################################################################
def ollama(state: State, config: RunnableConfig):


    llm = get_llm(config)
    configurable = Config.from_runnable_config(config)

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

    # Call the LLM with the full conversation history
    response = llm.stream(state.messages)

    # Join all chunks into a single response
    full_response = "".join(chunk.content for chunk in response)

    # Add the assistant's response to the message history
    assistant_message = {"role": "assistant", "content": full_response}
    state.messages.append(assistant_message)

    print('='*40)
    print("THE ASSISTANT SAID..")
    print(assistant_message)
    print('='*40)

    # Return the updated messages list with the new response
    return {"messages": [assistant_message]}




# def ollama(state: State, config: RunnableConfig):
#     # llm = get_llm(config)
#     # configurable = Config.from_runnable_config(config)
    
#     llm = ChatOllama(
#         model="llama3.1:8b",
#         keep_alive=-1,
#         # temperature=configurable.temperature / 100,
#         base_url=OLLAMA_HOST,
#         stream=True
#     )

#     response = llm.stream(state.messages)
    
#     # Join all chunks into a single response
#     full_response = "".join(chunk.content for chunk in response)
#     # Add the assistant's response to the message history
#     assistant_message = {"role": "assistant", "content": full_response}
#     state.messages.append(assistant_message)
    
#     # Return the updated messages list with the new response
#     return {"messages": [assistant_message]}
