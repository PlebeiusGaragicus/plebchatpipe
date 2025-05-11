from enum import Enum

OLLAMA_HOST = "http://host.docker.internal:11434"

class KeepAlive(str, Enum):
    NONE = "0"
    FIVE_MINUTES = "5m"
    FOREVER = "-1"


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
