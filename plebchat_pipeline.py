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
from typing import List, Union, Generator, Iterator, Literal


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


class Pipeline:
    class Valves(BaseModel):
        #TODO: how can we dynamically create a Literal type at runtime?  We can populate it with models Ollama has downloaded
        #TODO: The description field doesn't show up in OUI...
        LLM_MODEL: Literal[DEFAULT_OLLAMA_MODEL, 'phi4-mini:3.8b-q8_0', 'qwen3:4b-q8_0'] = Field(default=DEFAULT_OLLAMA_MODEL, description="LLM model to use")
        KEEP_ALIVE: Literal["-1", "0", "5m"] = Field("5m", description="How long to keep the model in memory")

        DISABLE_COMMANDS: bool = Field(False, description="Whether to disable commands (i.e. starts with '/')")
        PLEB_SERVER_URL: str = Field(default="http://host.docker.internal:9000", description="PlebChat server URL")
        OLLAMA_BASE_URL: str = Field(default="http://host.docker.internal:11434", description="Ollama server URL")
        DEBUG: bool = Field(default=False, description='run pipe in debug mode?')


    def __init__(self):
        self.type = "manifold"
        # This is prefixed onto each of the manifold agent names
        #NOTE: if the pipeline models are edited in OUI and their pipeline name changes.. it doesn't update.  This is a bug of OUI
        self.name = "PlebChat: "
        # self.name = "🗣️🤖💬 - "
        self.chat_id = None

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

    # async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
    #     # if self.valves.debug:
    #     #     print(f"[DEBUG] Received request: {json.dumps(body, indent=2)}")

    #     metadata = body.get("metadata", {})
    #     chat_id = metadata.get("chat_id", str(uuid.uuid4()))
    #     metadata["chat_id"] = chat_id
    #     body["metadata"] = metadata
    #     return body

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
        print(body)
        print("*"*30)
        print("MESSAGES")
        print(json.dumps(messages, indent=2))
        print("*"*30)

        valve_config = self.valves.model_dump()

        data = {
            "query": user_message,  # Include the original user query
            "messages": messages,
            "config": valve_config  # Include all valve settings as config
            }

        headers = {
            'accept': 'text/event-stream',
            'Content-Type': 'application/json',
        }

        try:
            #TODO: pass in valves as "config"
            response = requests.post(
                self.valves.PLEB_SERVER_URL + f"/graph/{model_id}",
                json=data,
                headers=headers,
                stream=True,
                timeout=5.0  # 5 seconds timeout for connection attempt
            )
            response.raise_for_status()
            return response.iter_lines()


        except Exception as e:
            print(f"ERROR: pipeline connection failed: {str(e)}")
            # Return a generator that yields error messages
            return error_generator(e, self.valves.PLEB_SERVER_URL)
