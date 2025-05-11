import os
from typing import Optional, Any
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableConfig



class Config(BaseModel):
    """The configurable fields for the graph."""
    LLM_MODEL: str = Field(default="llama3.1:8")
    KEEP_ALIVE: str = Field(default="5m")

    DISABLE_COMMANDS: bool = Field(default=False)
    PLEB_SERVER_URL: str = Field(default="http://host.docker.internal:9000")
    OLLAMA_BASE_URL: str = Field(default="http://host.docker.internal:11434")
    DEBUG: bool = Field(default=False)

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
