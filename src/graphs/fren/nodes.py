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
        writer(write_content(cmd_output.cmdOutput))
        return

    else:
        # The output should be processed by an LLM before returning to the user
        writer(write_thought(f"Processing command output with LLM..."))
        writer(write_thought( '---' ))
        writer(write_thought( "### command output:" ))
        writer(write_thought( cmd_output.cmdOutput ))


        # Create prompt for LLM
        prompt = cmd_output.reinjectionPrompt or "Process this information and provide a helpful response:"

        # Get the LLM

        # Prepare messages for the LLM
        messages = [
            {"role": "system", "content": cmd_output.reinjectionPrompt},
            {"role": "user", "content": f"{prompt}\n\n{cmd_output.cmdOutput}"}
        ]

        llm = get_llm(config)
        response = llm.stream(state.messages)

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
def ollama(state: State, config: RunnableConfig):


    # llm = get_llm(config)
    # configurable = Config.from_runnable_config(config)

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
    llm = get_llm(config)
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
