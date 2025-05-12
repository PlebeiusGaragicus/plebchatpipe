from enum import Enum

# OLLAMA_HOST = "http://host.docker.internal:11434"

# class KeepAlive(str, Enum):
#     NONE = "0"
#     FIVE_MINUTES = "5m"
#     FOREVER = "-1"


class NodeOutputType(str, Enum):
    """Enum for node output types used in LangGraph node metadata.
    
    These values determine how the output is displayed in the UI:
    - THOUGHT: Shows output as thinking/reasoning (typically in a different style)
    - ANSWER: Shows output as normal content to the user
    """
    THOUGHT = "thought"
    ANSWER = "answer"


#NOTE: These are used with LangGraph StreamWriter
#TODO: improve documentation
def write_thought(content: str):
    return {
        'type': 'thought',
        'content': f"{content}\n"
    }

def write_content(content: str):
    return {
        'type': 'content',
        'content': content
    }
