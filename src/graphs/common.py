import json
from enum import Enum
from typing import Callable


class NodeOutputType(str, Enum):
    """Enum for node output types used in LangGraph node metadata.
    
    These values determine how the output is displayed in the UI:
    - THOUGHT: Shows output as thinking/reasoning (typically in a different style)
    - ANSWER: Shows output as normal content to the user
    """
    THOUGHT = "thought"
    ANSWER = "answer"


#NOTE: These are used with LangGraph StreamWriter
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

def json_serializable(obj):
    """Convert an object to a JSON serializable format.
    
    Handles non-serializable objects by converting them to their string representation.
    """
    if isinstance(obj, dict):
        return {k: json_serializable(v) for k, v in obj.items() if not k.startswith('__')}
    elif isinstance(obj, list):
        return [json_serializable(item) for item in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        # For non-serializable objects, return their string representation
        return str(obj)

def think_codeblock(content, writer: Callable):
    """Display a code block in the UI with proper JSON formatting.
    
    Handles non-serializable objects by converting them to their string representation.
    """
    # Convert the content to a JSON serializable format
    serializable_content = json_serializable(content)
    
    # Format as JSON and display in a code block
    writer(write_thought(f"\n```json\n{json.dumps(serializable_content, indent=2)}\n```\n"))