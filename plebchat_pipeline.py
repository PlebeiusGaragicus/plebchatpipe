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


import json
import uuid
import requests
from pydantic import BaseModel, Field
from typing import List, Union, Generator, Iterator, Optional


class Pipeline:
    class Valves(BaseModel):
        debug: bool = Field(default=False, description='run pipe in debug mode?')
        PLEB_SERVER_URL: str = Field(default="http://host.docker.internal:9000", description="PlebChat server URL")
        # API_URL: str = Field(default="http://host.docker.internal:9000/stream", description="Langgraph API URL")

    def __init__(self):
        self.type = "manifold"
        self.name = "PlebChat: "
        # self.id = "Plebchat"
        self.chat_id = None

        # self.valves = self.Valves(
        #     **{k: os.getenv(k, v.default) for k, v in self.Valves.model_fields.items()}
        # )
        self.valves = self.Valves()
        self.set_pipelines()
        pass

    async def on_startup(self):
        print(f"PIPE: on_startup: {__name__}")
        pass

    async def on_shutdown(self): 
        print(f"PIPE: on_shutdown: {__name__}")
        pass


    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        if self.valves.debug:
            print(f"[DEBUG] Received request: {json.dumps(body, indent=2)}")

        metadata = body.get("metadata", {})
        chat_id = metadata.get("chat_id", str(uuid.uuid4()))
        metadata["chat_id"] = chat_id
        body["metadata"] = metadata

        return body

    def set_pipelines(self):
        self.pipelines = [
            {"id": "fren", "name": "🐸"}
            {"id": "crab", "name": "🦀"}
        ]
        # return [
        #     {"id": "fren", "name": "fren"}
        # ]
        pass

    def pipe(
        self, 
        user_message: str, 
        model_id: str, 
        messages: List[dict], 
        body: dict
            ) -> Union[str, Generator, Iterator]:

        print("*"*30)
        # print(f"chat_id: {self.chat_id}")
        # print("*"*30)
        # print(f"message_id: {self.message_id}")
        print("*"*30)
        print(user_message)
        print("*"*30)
        print(model_id)
        print("*"*30)
        print(body)
        print("*"*30)

        data = {
            "messages": [[msg['role'], msg['content']] for msg  in messages],
            }

        headers = {
            'accept': 'text/event-stream',
            'Content-Type': 'application/json',
        }

        response = requests.post(self.valves.PLEB_SERVER_URL + f"/{model_id}", json=data, headers=headers, stream=True)

        response.raise_for_status()

        return response.iter_lines()
