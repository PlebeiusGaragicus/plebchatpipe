import json
from typing import Literal
import tiktoken

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

from langgraph.types import StreamWriter

from graphs import configuration
from graphs.fren.state import State, SYSTEM_PROMPT
from graphs.fren.commands import CommandHandler
from graphs.common import answer, think, think_codeblock

############################################################################
# HELPER FUNCTIONS
############################################################################
def get_llm(config: RunnableConfig):
    configurable = configuration.Configuration.from_runnable_config(config)

    return ChatOllama(
        # model=configurable.OLLAMA_LLM_CHATMODEL,
        model="llama3.2:3b-instruct-q8_0",
        keep_alive=configurable.OLLAMA_KEEP_ALIVE,
        base_url=configurable.OLLAMA_BASE_URL,
        # num_ctx=131072 # FULL CONTEXT FOR LLAMA3.2 # 42GB of VRAM FOR KV CACHE!!!
        num_ctx=32768 # 1/4 context - 15GB KV CACHE
    )


############################################################################
# CONDITIONAL NODE
############################################################################
def check_for_command(state: State, config: RunnableConfig) -> Literal["handle_command", "ollama"]:
    """
        NOTE: This is the first conditional node on our graph
        It checks if the last message (aka user query) starts with a '/'.
        This function is prefixed with a '_' so that it's progress doesn't show in the frontend UI
    """

    if state.query.startswith("/"):
        return "handle_command"
    return "ollama"


############################################################################
# NODE
############################################################################
def init(state: State, config: RunnableConfig, writer: StreamWriter):
    configurable = configuration.Configuration.from_runnable_config(config)
    if configurable.DEBUG:
        # Display configuration as a code block
        think_codeblock( configurable.__dict__, writer=writer )
        think_codeblock( state, writer=writer )
        think('---', writer=writer)

    # calculate tokens of state.messages using a proper tokenizer
    try:
        # Try to use tiktoken for accurate token counting (works well for OpenAI models)
        # For Llama models this is an approximation but better than character counting
        enc = tiktoken.get_encoding("cl100k_base")  # cl100k_base is used by gpt-4/3.5-turbo
        total_tokens = 0
        for message in state.messages:
            # Count tokens in the message content
            if 'content' in message and message['content']:
                total_tokens += len(enc.encode(message['content']))
            # Also count tokens in the role (small overhead per message)
            if 'role' in message and message['role']:
                total_tokens += len(enc.encode(message['role']))

        if configurable.DEBUG:
            think(f"Total tokens in conversation: {total_tokens}/{32768} = `{total_tokens / 32768 * 100:0.2f}%`", writer=writer)
    except Exception as e:
        # Fallback to a simpler estimation if tiktoken is not available
        if configurable.DEBUG:
            think(f"Error calculating tokens: {str(e)}", writer=writer)
        total_tokens = sum(len(m.get('content', '')) // 4 for m in state.messages)  # Rough estimate: ~4 chars per token

    # query = state.messages[-1]['content']
    # return {"query": query}
    return {}


############################################################################
# NODE
############################################################################
def handle_command(state: State, config: RunnableConfig, writer: StreamWriter):
    # extract command
    split = state.query.split(" ")

    # Remove the slash and take the first word
    command = split[0][1:].lower()
    arguments = split[1:]

    if not command:
        command = ""

    configurable = configuration.Configuration.from_runnable_config(config)
    if configurable.DEBUG == True:
        think(f"Running `{command}` with arguments {arguments}", writer=writer)
        think('---', writer=writer)

    # Get command output
    cmd_output = CommandHandler._run(command, arguments)

    # Handle the command output based on its properties
    if cmd_output.returnDirect:
        # Access the cmdOutput property of the CommandOutput object
        output_content = cmd_output.cmdOutput
        answer(output_content, writer=writer)
        return

        # assistant_message = {"role": "assistant", "content": cmd_output.cmdOutput}
        # state.messages.append(assistant_message)
        # return {"messages": [assistant_message]}

    # The output should be processed by an LLM before returning to the user
    think("Processing command output with LLM...", writer=writer)
    think('---', writer=writer)
    think("### command output:", writer=writer)
    think(cmd_output.cmdOutput, writer=writer)
    think('---', writer=writer)


    # Create prompt for LLM
    prompt = cmd_output.reinjectionPrompt or "Process this information and provide a helpful response:"

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
def ollama(state: State, config: RunnableConfig, writer: StreamWriter):

    # If we have a new user query, add it to the messages
    # if state.query:
    #     # Add the user's query to the message history
    #     user_message = {"role": "user", "content": state.query}
    #     # Ensure we're not duplicating the message if it's already in the state
    #     if not state.messages or state.messages[-1] != user_message:
    #         state.messages.append(user_message)

    # Add system prompt to messages if it's not already there
    if state.messages[0].get("role") != "system":
        state.messages = [{"role": "system", "content": SYSTEM_PROMPT}] + state.messages

    print( "#"* 40)
    print( state.messages )
    # think( state.messages, writer=writer )

    # Call the LLM with the full conversation history
    llm = get_llm(config)
    response = llm.stream(state.messages)

    # Join all chunks into a single response
    full_response = "".join(chunk.content for chunk in response)

    # Add the assistant's response to the message history
    assistant_message = {"role": "assistant", "content": full_response}
    state.messages.append(assistant_message)

    # Return the updated messages list with the new response
    return {"messages": [assistant_message]}
