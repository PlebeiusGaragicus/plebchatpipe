import json
import asyncio
import operator
import requests
import traceback
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Any, Annotated, Dict, List

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from graphs.common import OLLAMA_HOST


class State(BaseModel):
    messages: Annotated[list, operator.add] = Field(default_factory=list)




app = FastAPI(
    title="Langgraph API",
    description="Langgraph API",
    )

@app.get("/health")
def health_check():
    """Health check endpoint for Docker healthcheck"""
    return {"status": "healthy"}

def thinking_tokens(tokens: str):
    return {
        'choices': 
        [
            {
                'delta':
                {
                    'reasoning_content': tokens, 
                },
                'finish_reason': None                            
            }
        ]
    }

def thinking_newline():
    return {
        'choices': 
        [
            {
                'delta':
                {
                    'reasoning_content': "\n",
                },
                'finish_reason': None
            }
        ]
    }

def content_tokens(tokens: str):
    return {
        'choices': 
        [
            {
                'delta':
                {
                    'content': tokens, 
                },
                'finish_reason': None
            }
        ]
    }

def newlines():
    return {
        'choices': 
        [
            {
                'delta':
                {
                    'content': "\n\n",
                },
                'finish_reason': None
            }
        ]
    }

@app.get("/graphs")
async def get_graphs():
    from graphs import all_graphs

    return all_graphs


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
async def stream(graph_id: str, messages: State):
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
        await asyncio.sleep(0)  # Force flush

        current_node = None
        config = {}
        
        try:
            stream_generator = agent.stream(input=messages, config=config, stream_mode=["messages", "custom"])
            for event, data in stream_generator:
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


                if event == "custom":
                    content_type = data['type']
                    msg = data['content']

                    if content_type == "thought":
                        yield f"data: {json.dumps(thinking_newline())}\n\n"
                        yield f"data: {json.dumps( thinking_tokens( msg ) )}\n\n"

                    else:
                        # title = data['title']
                        yield f"data: {json.dumps(newlines())}\n\n"
                        #TODO: only write node name if in DEBUG mode
                        # yield f"data: {json.dumps(content_tokens('---'))}\n\n"
                        # yield f"data: {json.dumps(newlines())}\n\n"
                        # yield f"data: {json.dumps( content_tokens( f'## {title}') )}\n\n"
                        # yield f"data: {json.dumps(newlines())}\n\n"
                        yield f"data: {json.dumps( content_tokens( msg ) )}\n\n"

                if event == "messages":
                    reply_content = data[0]
                    metadata = data[1]


                    # Handle node change
                    if current_node != metadata["langgraph_node"]:
                        current_node = metadata["langgraph_node"]
                        print(f"node: {current_node}")
                        
                        # Output the node name as a header based on node type
                        if 'node_output_type' in metadata and metadata['node_output_type'] == "thought":
                            # For thought nodes, use thinking_tokens for the header
                            # if current_node is not None:
                                # yield f"data: {json.dumps(thinking_newline())}\n\n"
                                # yield f"data: {json.dumps(thinking_tokens('---'))}\n\n"
                            # yield f"data: {json.dumps(thinking_tokens('_'*len(current_node)))}\n\n"
                            # yield f"data: {json.dumps(thinking_newline())}\n\n"
                            # yield f"data: {json.dumps(thinking_tokens(f'### `{current_node}`'))}\n\n"
                            # yield f"data: {json.dumps(thinking_newline())}\n\n"
                            pass
                        else:
                            # For answer nodes or default, use content_tokens
                            # yield f"data: {json.dumps(content_tokens(f'## {current_node}'))}\n\n"
                            # yield f"data: {json.dumps(newlines())}\n\n"
                            pass


                    if hasattr(reply_content, 'content') and reply_content.content:
                        # print(f"{reply_content.content}", end='', sep='|', flush=True)
                        # print(f"{reply_content.content}", end='|', flush=False)
                        print(reply_content.content)

                        if 'node_output_type' in metadata and metadata['node_output_type'] == "thought":
                            content_msg = thinking_tokens(reply_content.content)
                        else:
                            content_msg = content_tokens(reply_content.content)

                        yield f"data: {json.dumps(content_msg)}\n\n"
                        await asyncio.sleep(0)


                # End of the stream
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
            print(f"ERROR in graph execution: {error_msg}\n{stack_trace}")
            
            # Send the error as a content message to the frontend
            error_content = f"⚠️ Error in graph execution: {error_msg}"
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
