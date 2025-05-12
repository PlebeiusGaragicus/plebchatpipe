import json
from enum import Enum
from typing import Callable

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

def answer(content, writer: Callable):
    writer( write_content( f"\n{content}\n" ) )

def think(content, writer: Callable):
    writer( write_thought( f"\n{content}\n" ) )

def think_codeblock(content: str, writer: Callable):
    writer( write_thought( f"\n```\n{json.dumps(content, indent=2)}\n```\n" ) )
