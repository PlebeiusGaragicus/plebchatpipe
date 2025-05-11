import json


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


def emit_event(description: str, done: bool):
    event = {
            "event": {
                "type": "status",
                "data": {
                    "description": description,
                    "done": done,
                },
            }
        }
    return f"data: {json.dumps(event)}\n\n"
