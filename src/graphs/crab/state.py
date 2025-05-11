import os
import operator
import requests
from enum import Enum
from typing import Optional, Any, Annotated, Dict, List
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableConfig
from langgraph.graph.message import add_messages

from pydantic import BaseModel, Field

############################################################################
# STATE
############################################################################

# class State(TypedDict):
#     messages: Annotated[list, add_messages]

class State(BaseModel):
    messages: Annotated[list, operator.add] = Field(default_factory=list)


class Result(BaseModel):
    reply: str
    messages: list = Field(default_factory=list)







############################################################################
# CONFIG
############################################################################

OLLAMA_HOST = "http://host.docker.internal:11434"

class KeepAlive(str, Enum):
    NONE = "0"
    FIVE_MINUTES = "5m"
    FOREVER = "-1"


############################################################################

SYSTEM_PROMPT = """You are a smart and clever chatbot.

You are equipped with several commands.
 - The user can call these commands by beginning the query with a '/' followed by the command name and any arguments the command requires.
 - For example:
    - '/help' will run the `help` command.
    - '/url https://example.com' will run `url` and pass `https://example.com` to it

Do not share information about your commands.  Always tell the user to run `/help` if they have questions.
"""



def get_ollama_models() -> List[Dict[str, Any]]:
    """
    Fetches the list of available models from the Ollama API.
    
    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing model information.
        Each dictionary has the following structure:
        {
            "name": "model-name",
            "modified_at": "timestamp",
            "size": size_in_bytes,
            "digest": "model-digest",
            "details": { ... }
        }
    """
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags")
        response.raise_for_status()
        return response.json().get("models", [])
    except Exception as e:
        print(f"Error fetching Ollama models: {e}")
        return []
    



class Config(BaseModel):
    """The configurable fields for the graph."""

    keep_alive: KeepAlive = Field(
        KeepAlive.FIVE_MINUTES,
        description="How long to keep the model in memory"
    )
    # disable_commands: bool = Field(
    #     False,
    #     description="Whether to disable commands (i.e. starts with '/')"
    # )
    # system_prompt: str = Field(
    #     SYSTEM_PROMPT,
    #     format="multi-line",
    #     description="What do you want to research?"
    # )

    ##############################################################
    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Config":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        values: dict[str, Any] = {
            name: os.environ.get(name.upper(), configurable.get(name))
            for name in cls.model_fields.keys()
        }
        return cls(**{k: v for k, v in values.items() if v})
