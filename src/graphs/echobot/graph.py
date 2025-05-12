"""This 'ollama' graph outlines a LangGraph agent with memory functionality."""

import os
import operator
from pydantic import BaseModel, Field
from typing import Optional, Any, Annotated

from langgraph.graph.state import StateGraph
from langchain_core.runnables import RunnableConfig
from langgraph.types import StreamWriter

from ..common import write_content, write_thoughts, NodeOutputType


class State(BaseModel):
    messages: Annotated[list, operator.add] = Field(default_factory=list)


class Config(BaseModel):
    """The configurable fields for the graph."""
    #TODO: ...
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




#NOTE: since we aren't using an LLM to generate tokens, we need to use the writer to print to the UI
def echo(state: State, config: RunnableConfig, writer: StreamWriter):
    writer( write_thoughts( "Geesh... this guy's an idiot amirite?" ) )

    echoback = state.messages[-1]['content']
    writer( write_content( echoback ) )



graph_builder = StateGraph(State, input=State, config_schema=Config)

graph_builder.add_node("echo", echo, metadata={"node_output_type": NodeOutputType.ANSWER})
graph_builder.add_edge("__start__", "echo")
graph_builder.add_edge("echo", "__end__")

graph = graph_builder.compile()
