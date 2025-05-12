# from enum import Enum

# OLLAMA_HOST = "http://host.docker.internal:11434"

# class KeepAlive(str, Enum):
#     NONE = "0"
#     FIVE_MINUTES = "5m"
#     FOREVER = "-1"


#NOTE: These are used with LangGraph StreamWriter
#TODO: improve documentation
def write_thoughts(content: str):
    return {
        'type': 'thought',
        'content': f"{content}\n"
    }

def write_content(content: str):
    return {
        'type': 'content',
        'content': content
    }
