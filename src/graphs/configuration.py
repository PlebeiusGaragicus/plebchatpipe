"""The configurable fields for our graphs."""

import os
from typing import Optional, Any
from dataclasses import dataclass, fields

from langchain_core.runnables import RunnableConfig

@dataclass(kw_only=True)
class Configuration:
    # NOTE: these should mirror the Valves from our Open WebUI pipeline - 'plebchat_pipeline.py'
    DEBUG: bool = True

    # OLLAMA_KEEP_ALIVE: str = "5m"
    # OLLAMA_LLM_CHATMODEL: str = "llama3.1:8"
    # OLLAMA_LLM_TOOLMODEL: str = "llama3.1:8"
    # OLLAMA_LLM_CODEMODEL: str = "llama3.1:8"
    # OLLAMA_LLM_SMARTMODEL: str = "llama3.1:8"

    # PLEB_SERVER_URL: str = "http://host.docker.internal:9000"
    # OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"
    # SEARXNG_URL: str = "http://host.docker.internal:4001"

    # TAVILY_API_KEY: str = None
    
    def __repr__(self) -> str:
        """Custom representation that includes all attributes, even dynamically added ones."""
        # Skip attributes that start with double underscores
        attrs = [f"{k}={repr(v)}" for k, v in self.__dict__.items() if not k.startswith('__')]
        return f"Configuration({', '.join(attrs)})"

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig.
        
        This method will create a Configuration instance using values from:
        1. Environment variables (highest priority)
        2. Values in the config["configurable"] dictionary
        3. Default values defined in the class (lowest priority)
        
        Additionally, any keys in config["configurable"] that aren't defined as fields
        in the Configuration class will be added as attributes to the instance.
        """
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        
        # Get values for the defined fields
        values: dict[str, Any] = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
            if f.init
        }
        
        # Don't filter out False values - keep all values that are not None
        instance = cls(**{k: v for k, v in values.items() if v is not None})

        # Add any additional attributes that aren't defined as fields
        defined_fields = {f.name for f in fields(cls)}
        for key, value in configurable.items():
            if key not in defined_fields and value is not None:
                setattr(instance, key, value)
                
        return instance