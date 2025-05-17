"""
title: PlebChat
author: PlebbyG
author_url: https://github.com/PlebeiusGaragicus
git_url: https://github.com/PlebeiusGaragicus/plebchatpipe
description: Custom-built agents for everyday plebs, like me!
required_open_webui_version: 0.4.3
requirements: none
version: 0.0.1
licence: MIT
"""


################################################
DEFAULT_OLLAMA_MODEL = "llama3.1:8b"



################################################


import json
import uuid
import requests
from pydantic import BaseModel, Field
from typing import List, Union, Generator, Iterator, Literal, Optional


def error_generator(e, server_url):
    """Generator function that yields error messages in the expected format.
    
    Args:
        e: The exception that occurred
        server_url: The URL of the server that failed to connect
        
    Yields:
        Formatted error messages that match the expected response format
    """
    # Yield the status event
    yield {
        "event": {
            "type": "status",
            "data": {
                "description": "🚨 GRAPH EXECUTION HALTED!",
                "done": True,
            },
        }
    }
    # Yield a simple error message with the actual exception text
    yield f"Connection to server failed: `{type(e).__name__}`\n"
    yield f"```\n{str(e)}\n```\n"
    yield f"Please check if the server at {server_url} is running."
    # End the stream with an error finish reason
    stream_end = {
        'choices': [
            {
                'delta': {},
                'finish_reason': 'error'
            }
        ]
    }
    yield f"data: {json.dumps(stream_end)}\n\n"


class Pipeline:
    class Valves(BaseModel):
        DEBUG: bool = Field(default=True, description='run pipe in debug mode?')

        #TODO: how can we dynamically create a Literal type at runtime?  We can populate it with models Ollama has downloaded
        #TODO: The description field doesn't show up in OUI...
        OLLAMA_KEEP_ALIVE: Literal["-1", "0", "5m"] = Field("5m", description="How long to keep the model in memory")
        OLLAMA_LLM_CHATMODEL: Literal[DEFAULT_OLLAMA_MODEL, 'phi4-mini:3.8b-q8_0', 'qwen3:4b-q8_0'] = Field(default=DEFAULT_OLLAMA_MODEL, description="LLM model to use")
        OLLAMA_LLM_TOOLMODEL: Literal[DEFAULT_OLLAMA_MODEL, 'phi4-mini:3.8b-q8_0', 'qwen3:4b-q8_0'] = Field(default=DEFAULT_OLLAMA_MODEL, description="LLM model to use")
        OLLAMA_LLM_CODEMODEL: Literal[DEFAULT_OLLAMA_MODEL, 'phi4-mini:3.8b-q8_0', 'qwen3:4b-q8_0'] = Field(default=DEFAULT_OLLAMA_MODEL, description="LLM model to use")
        OLLAMA_LLM_SMARTMODEL: Literal[DEFAULT_OLLAMA_MODEL, 'phi4-mini:3.8b-q8_0', 'qwen3:4b-q8_0'] = Field(default=DEFAULT_OLLAMA_MODEL, description="LLM model to use")

        PLEB_SERVER_URL: str = Field(default="http://host.docker.internal:9000", description="PlebChat server URL")
        OLLAMA_BASE_URL: str = Field(default="http://host.docker.internal:11434", description="Ollama server URL")
        SEARXNG_URL: str = Field(default="http://host.docker.internal:4001", description="SearXNG API URL")

        TAVILY_API_KEY: str = Field(default="NOT_SET", description="Tavily API key")


    def __init__(self):
        self.type = "manifold"
        self.name = "PlebChat: " # This is prefixed onto each of the manifold agent names
        #NOTE: if the pipeline models are edited in OUI and their pipeline name changes.. it doesn't update.  This is a bug/issue of OUI

        #NOTE: we will define our own variables (outside of `body`, `message`, etc) that will persist along the lifespan of the call
        self.metadata = None
        self.thread_id = None

        self.valves = self.Valves()
        self.set_pipelines()
        pass

    async def on_startup(self):
        print(f"PIPE: on_startup: {__name__}")
        pass

    async def on_shutdown(self):
        print(f"PIPE: on_shutdown: {__name__}")
        pass

    async def on_valves_updated(self):
        self.set_pipelines()
        pass

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        if self.valves.DEBUG:
            print(f"[PIPELINE INLET] body: {json.dumps(body, indent=2)}")
            print(f"[PIPELINE INLET] user: {json.dumps(user, indent=2)}")

        metadata = body.get("metadata", {})
        self.metadata = metadata
        self.thread_id = metadata.get("chat_id", str(uuid.uuid4()))

        # not sure what these do... they don't seem to "stick"
        # metadata["chat_id"] = chat_id
        # body["metadata"] = metadata
        return body

    def set_pipelines(self):
        #TODO: This fails (and ultimately the pipeline cannot be loaded into OUI) if the fkn server isn't running!! THAT SUCKS!
        try:
            # Try to get available graphs/agents from the server
            # response = requests.get(self.valves.PLEB_SERVER_URL + "/graphs")
            response = requests.get("http://host.docker.internal:9000/graphs")
            response.raise_for_status()
            server_models = response.json()

            # Update pipelines with models from server if available
            if server_models and isinstance(server_models, list):
                self.pipelines = server_models
                if self.valves.DEBUG:
                    print(f"[DEBUG] Models loaded from server: {json.dumps(server_models, indent=2)}")
        except Exception as e:
            print(f"[WARNING] Failed to fetch models from server: {str(e)}")
            print("[INFO] Using default models")
            raise
        pass

    def pipe(
        self, 
        user_message: str, 
        model_id: str, 
        messages: List[dict], 
        body: dict
            ) -> Union[str, Generator, Iterator]:

        # print("*"*30)
        # print(f"chat_id: {self.chat_id}")
        # print("*"*30)
        # print(f"message_id: {self.message_id}")
        # print("*"*30)
        # print(user_message)
        # print("*"*30)
        # print(model_id)
        print("*"*30)
        print("MESSAGES")
        print(json.dumps(messages, indent=2))
        print("*"*30)
        print(body)
        print("*"*30)
        print("thread_id:")
        print(self.thread_id)
        print("*"*30)
        print("metadata:")
        print(json.dumps(self.metadata, indent=2))
        print("*"*30)

        data = {
            "query": user_message,  # Include the original user query
            "messages": messages,
            "config": self.valves.model_dump()  # Include all valve settings as config
        }

        data['config']['thread_id'] = self.thread_id
        print("*"*30)
        print("THIS IS THE FINAL VERSION OF THE DATA PAYLOAD THAT WILL BE SENT")
        print(json.dumps(data, indent=2))
        print("*"*30)

        headers = {
            'accept': 'text/event-stream',
            'Content-Type': 'application/json',
        }

        try:
            response = requests.post(
                self.valves.PLEB_SERVER_URL + f"/graph/{model_id}",
                json=data,
                headers=headers,
                stream=True,
                timeout=10.0  # 5 seconds timeout for connection attempt
            )
            response.raise_for_status()
            return response.iter_lines()

        except Exception as e:
            print(f"ERROR: pipeline connection failed: {str(e)}")
            # Return a generator that yields error messages
            return error_generator(e, self.valves.PLEB_SERVER_URL)