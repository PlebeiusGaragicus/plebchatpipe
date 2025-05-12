"""
The configurable fields for our graphs.

NOTE: this should mirror the Valves from our Open WebUI pipeline - 'plebchat_pipeline.py'
"""

import os
from typing import Optional, Any
from dataclasses import dataclass, fields

from langchain_core.runnables import RunnableConfig

@dataclass(kw_only=True)
class Configuration:
    DEBUG: bool = True

    OLLAMA_KEEP_ALIVE: str = "5m"
    OLLAMA_LLM_CHATMODEL: str = "llama3.1:8"
    OLLAMA_LLM_TOOLMODEL: str = "llama3.1:8"
    OLLAMA_LLM_CODEMODEL: str = "llama3.1:8"
    OLLAMA_LLM_SMARTMODEL: str = "llama3.1:8"

    PLEB_SERVER_URL: str = "http://host.docker.internal:9000"
    OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"
    SEARXNG_URL: str = "http://host.docker.internal:4001"

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        values: dict[str, Any] = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
            if f.init
        }
        # Don't filter out False values - keep all values that are not None
        return cls(**{k: v for k, v in values.items() if v is not None})