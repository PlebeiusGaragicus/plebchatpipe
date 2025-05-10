from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

from langgraph.types import StreamWriter

from .state import State, Config, OLLAMA_HOST
from .commands import CommandHandler

############################################################################
# HELPER FUNCTIONS
############################################################################
def get_llm(config: RunnableConfig):
    configurable = Config.from_runnable_config(config)
    return ChatOllama(
        model=configurable.model,
        keep_alive=configurable.keep_alive,
        temperature=configurable.temperature / 100,
        base_url=OLLAMA_HOST,
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
    query = state.messages[-1][-1]
    print(query)
    if query.startswith("/"):
        return "handle_command"
    return "thick"


############################################################################
# NODE
############################################################################
def handle_command(state: State, config: RunnableConfig):
    # configurable = Config.from_runnable_config(config)

    # extract command
    query = state.messages[-1]
    split = query.split(" ")
    # Remove the slash and take the first word
    command = split[0][1:].lower()
    arguments = split[1:]

    # check if command is empty
    if not command:
        command = ""
        # return {"messages": [{"role": "assistant", "content": "⚠️ Please provide a command.\n\n**Example:**\n```\n/help\n```"}]}
    

    # Use CommandHandler class method directly
    response = CommandHandler._run(command, arguments)

    return {"messages": [{"role": "assistant", "content": response}]}


def write_thoughts(content: str):
    return {
        'type': 'thought',
        'content': content
    }

def write_content(content: str):
    return {
        'type': 'content',
        'content': content
    }



def thick(state: State, config: RunnableConfig, writer: StreamWriter):
    print("nothing node nothing node nothing node nothing node nothing node")

    thoughts = """
I have many THICK thoughts...
    """

    # writer( write_thoughts(thoughts) )

    return {}

def nothing(state: State, config: RunnableConfig, writer: StreamWriter):
    print("nothing node nothing node nothing node nothing node nothing node")

    content = """

...


More content:

```python
def nothing(state: State, config: RunnableConfig, writer: StreamWriter):
    print("nothing node nothing node nothing node nothing node nothing node")
    return {}
    # writer(
```
    """

    writer( write_content(content) )

    return {}

# def nothing(state: State, config: RunnableConfig, writer: StreamWriter):
#     print("nothing node nothing node nothing node nothing node nothing node")
#     # return {}
#     writer(
#         {
#             'title': 'custom shit',
#             'content': 'THIS IS FROM MY NODE BROOOO'
#             }
#     )
#     assistant_message = {"role": "assistant", "content": "nothing"}
#     return {"messages": [assistant_message]}



############################################################################
# NODE
############################################################################
def ollama(state: State, config: RunnableConfig):
    # llm = get_llm(config)
    # configurable = Config.from_runnable_config(config)
    
    llm = ChatOllama(
        model="llama3.1:8b",
        keep_alive=-1,
        # temperature=configurable.temperature / 100,
        base_url=OLLAMA_HOST,
        stream=True
    )

    response = llm.stream([{"role": "user", "content": "hello, sir"}])
    
    # Join all chunks into a single response
    full_response = "".join(chunk.content for chunk in response)
    # Add the assistant's response to the message history
    assistant_message = {"role": "assistant", "content": full_response}
    state.messages.append(assistant_message)
    
    # Return the updated messages list with the new response
    return {"messages": [assistant_message]}


def thought_llama(state: State, config: RunnableConfig):
    # llm = get_llm(config)
    # configurable = Config.from_runnable_config(config)
    
    llm = ChatOllama(
        model="llama3.1:8b",
        keep_alive=-1,
        # temperature=configurable.temperature / 100,
        base_url=OLLAMA_HOST,
        stream=True
    )

    response = llm.stream(state.messages)
    
    # Join all chunks into a single response
    full_response = "".join(chunk.content for chunk in response)
    # Add the assistant's response to the message history
    assistant_message = {"role": "assistant", "content": full_response}
    state.messages.append(assistant_message)
    
    # Return the updated messages list with the new response
    return {"messages": [assistant_message]}
