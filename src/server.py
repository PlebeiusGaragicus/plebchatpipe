import json
import asyncio
import traceback
from pydantic import BaseModel, Field
from typing import Annotated, List, Dict, Any, Optional

from fastapi import FastAPI, Body
from fastapi.responses import StreamingResponse

from graphs.common import NodeOutputType
from helpers import content_tokens, newlines, thinking_tokens, thinking_newline, emit_event


# Define Pydantic models for request validation
class Message(BaseModel):
    role: str
    content: str

class GraphRequest(BaseModel):
    query: Optional[str] = None
    messages: List[dict]
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)



app = FastAPI(
    title="PlebChat Agents API",
    description="A collection of agents, implemented with LangGraph",
)


@app.get("/health")
def health_check():
    """Health check endpoint for Docker healthcheck"""
    return {"status": "healthy"}


@app.get("/graphs")
async def get_graphs():
    from graphs import all_graphs
    return all_graphs

OLLAMA_HOST = "http://host.docker.internal:11434"


@app.get("/models")
async def get_models():
    import requests
    
    try:
        ollama_url = f"{OLLAMA_HOST}/api/tags"

        response = requests.get(ollama_url)
        response.raise_for_status()

        # Extract the model names from the Ollama response
        ollama_data = response.json()
        models = []

        for model in ollama_data['models']:
            if 'embed' not in model['name']: # skip some embedding models
                models.append( model['name'] )

        return models
    except Exception as e:
        print(f"Error fetching Ollama models: {str(e)}")
        return {"error": f"Failed to fetch Ollama models: {str(e)}"}



@app.post("/graph/{graph_id}")
async def stream(graph_id: str, request: GraphRequest):

    print("*"*30)
    print("POST REQUEST TO THE GRAPH ENDPOINT")
    print("*"*30)
    
    # Detect if this is a tool selection call or a regular chat call
    is_tool_selection = False
    if request.messages and len(request.messages) >= 2:
        if request.messages[0].get('role') == 'system' and 'Available Tools' in request.messages[0].get('content', ''):
            is_tool_selection = True
    
    print(f"REQUEST TYPE: {'TOOL SELECTION' if is_tool_selection else 'REGULAR CHAT'}")
    print("*"*30)
    
    print(f"MESSAGES:")
    for m in request.messages:
        print(json.dumps(m, indent=2))
    print(f"CONFIG:")
    print(json.dumps(request.config, indent=2))
    if request.query:
        print(f"Query: {request.query}")
    print("*"*30)


    from graphs import graph_registry

    # Check if the requested graph exists
    if graph_id not in graph_registry:
        return {"error": f"Graph with ID '{graph_id}' not found"}

    # Get the appropriate graph based on the ID
    agent = graph_registry[graph_id]

    async def event_stream():
        # Start the stream with an empty delta to initialize the connection
        stream_start_msg = {
            'choices': [
                {
                    'delta': {}, 
                    'finish_reason': None
                }
            ]
        }
        yield f"data: {json.dumps(stream_start_msg)}\n\n"
        # await asyncio.sleep(0)  # Force flush

        yield emit_event("Running...", False)
        await asyncio.sleep(0)  # Force flush

        current_node = None
        
        try:
            # Format input according to the State model structure
            input_state = {
                "messages": request.messages,
                "query": request.query
            }
            
            for event, data in agent.stream(input=input_state, config=request.config, stream_mode=["messages", "custom"]):

                if event == "custom":
                    content_type = data['type']
                    msg = data['content']

                    if content_type == "thought":
                        yield f"data: {json.dumps(thinking_newline())}\n\n"
                        yield f"data: {json.dumps( thinking_tokens( msg ) )}\n\n"
                    else:
                        yield f"data: {json.dumps(newlines())}\n\n"
                        yield f"data: {json.dumps( content_tokens( msg ) )}\n\n"

                if event == "messages":
                    reply_content = data[0]
                    metadata = data[1]

                    # Handle node change
                    if current_node != metadata["langgraph_node"]:
                        current_node = metadata["langgraph_node"]
                        print(f"node: {current_node}")
                        nice_node_name = current_node.replace('_', ' ')
                        yield emit_event(f"Running... {nice_node_name}", False)
                        await asyncio.sleep(0)  # Force flush

                    if hasattr(reply_content, 'content') and reply_content.content:
                        # print(reply_content.content) #  show tokens as they stream

                        if 'node_output_type' in metadata and metadata['node_output_type'] == NodeOutputType.THOUGHT:
                            content_msg = thinking_tokens(reply_content.content)
                        else:
                            content_msg = content_tokens(reply_content.content)

                        yield f"data: {json.dumps(content_msg)}\n\n"
                        await asyncio.sleep(0)

            # yield emit_event("Completed", True)
            yield emit_event("", True)
            
            # End of the stream - moved outside the for loop
            stream_end_msg = {
                'choices': [
                    {
                        'delta': {},
                        'finish_reason': 'stop'
                    }
                ]
            }
            yield f"data: {json.dumps(stream_end_msg)}\n\n"


        except Exception as e:
            # Capture the error and send it to the frontend
            error_msg = str(e)
            stack_trace = traceback.format_exc()

            # Send the error as a content message to the frontend
            error_content = f"⚠️ Error in graph execution: {error_msg}"
            yield f"data: {json.dumps(content_tokens(error_content))}\n\n"
            yield f"data: {json.dumps(newlines())}\n\n"

            #TODO: ONLY IN DEBUG MODE!!! OTherwise we expose the working code of our app...
            error_content = f"```{stack_trace}```"
            yield f"data: {json.dumps(content_tokens(error_content))}\n\n"

            # End the stream with an error finish reason
            error_end_msg = {
                'choices': [
                    {
                        'delta': {},
                        'finish_reason': 'error'
                    }
                ]
            }
            yield f"data: {json.dumps(error_end_msg)}\n\n"
            yield emit_event("Graph error!", True)


    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no",  # Disable buffering in Nginx
            "Transfer-Encoding": "chunked"
        }
    )





                # print("===========================")
                # print(f"event type: {type(event)}")
                # print(f"data type: {type(data)}")

                # # Handle different data types appropriately
                # if isinstance(event, (dict, list, str, int, float, bool)) or event is None:
                #     print(f">>> >>> event:\n{json.dumps(event, indent=2)}")
                # elif isinstance(event, tuple):
                #     print(f">>> >>> event (tuple) of length {len(event)}:")
                #     for i, item in enumerate(event):
                #         print(f">>> >>> event[{i}] type: {type(item)}")
                #         if isinstance(item, (dict, list, str, int, float, bool)) or item is None:
                #             print(f">>> >>> event[{i}]:\n{json.dumps(item, indent=2)}")
                #         else:
                #             print(f">>> >>> event[{i}] (non-serializable object of type {type(item).__name__})")
                #             # Try to inspect object attributes in a structured way
                #             try:
                #                 attrs = [attr for attr in dir(item) if not attr.startswith('__') and not callable(getattr(item, attr))]
                #                 if attrs:
                #                     print(f">>> >>> event[{i}] attributes:")
                #                     for attr in attrs:
                #                         value = getattr(item, attr)
                #                         if isinstance(value, (dict, list, str, int, float, bool)) or value is None:
                #                             print(f">>> >>> event[{i}].{attr} = {value}")
                #                         else:
                #                             print(f">>> >>> event[{i}].{attr} = <{type(value).__name__}>")
                #             except Exception as e:
                #                 print(f">>> >>> Failed to inspect event[{i}]: {e}")
                # else:
                #     print(f">>> >>> event (non-serializable object of type {type(event).__name__}):\n{event}")
                #     # Try to inspect object attributes
                #     try:
                #         members = {attr: getattr(event, attr) for attr in dir(event) 
                #                 if not attr.startswith('__') and not callable(getattr(event, attr))}
                #         print(f">>> >>> event members:")
                #         for name, value in members.items():
                #             print(f">>> >>> event.{name} = {value}")
                #     except Exception as e:
                #         print(f">>> >>> Failed to inspect event object: {e}")
                    
                # if isinstance(data, (dict, list, str, int, float, bool)) or data is None:
                #     print(f">>> >>> data:\n{json.dumps(data, indent=2)}")
                # elif isinstance(data, tuple):
                #     print(f">>> >>> data (tuple) of length {len(data)}:")
                #     for i, item in enumerate(data):
                #         print(f">>> >>> data[{i}] type: {type(item)}")
                #         if isinstance(item, (dict, list, str, int, float, bool)) or item is None:
                #             print(f">>> >>> data[{i}]:\n{json.dumps(item, indent=2)}")
                #         else:
                #             print(f">>> >>> data[{i}] (non-serializable object of type {type(item).__name__})")
                #             # Try to inspect object attributes in a structured way
                #             try:
                #                 attrs = [attr for attr in dir(item) if not attr.startswith('__') and not callable(getattr(item, attr))]
                #                 if attrs:
                #                     print(f">>> >>> data[{i}] attributes:")
                #                     for attr in attrs:
                #                         value = getattr(item, attr)
                #                         if isinstance(value, (dict, list, str, int, float, bool)) or value is None:
                #                             print(f">>> >>> data[{i}].{attr} = {value}")
                #                         else:
                #                             print(f">>> >>> data[{i}].{attr} = <{type(value).__name__}>")
                #             except Exception as e:
                #                 print(f">>> >>> Failed to inspect data[{i}]: {e}")
                # else:
                #     print(f">>> >>> data (non-serializable object of type {type(data).__name__}):\n{data}")
                #     # Try to inspect object attributes
                #     try:
                #         members = {attr: getattr(data, attr) for attr in dir(data) 
                #                 if not attr.startswith('__') and not callable(getattr(data, attr))}
                #         print(f">>> >>> data members:")
                #         for name, value in members.items():
                #             print(f">>> >>> data.{name} = {value}")
                #     except Exception as e:
                #         print(f">>> >>> Failed to inspect data object: {e}")
