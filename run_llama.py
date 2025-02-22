

import requests
import os

def chat_with_llama3(messages, host=None, model="meta/llama-3.3-70b-instruct", max_tokens=64):
    host = host or os.getenv("LLAMA3HOST", "localhost")
    url = f"http://{host}:8000/v1/chat/completions"

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": messages,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
            "name": "threat_analysis",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                "threatReasoning": {
                    "type": "string",
                    "description": "Why this post is a cyber threat or not a cyber threat"
                },
                "isThreat": {
                    "type": "boolean",
                    "description": "Whether the post contains a cyber threat"
                },
                "description": {
                    "type": "string",
                    "description": "A short description of the threat if it is one, with bullet points"
                },
                "title": {
                    "type": "string",
                    "description": "A title describing the threat if it is one"
                }
                },
                "required": ["reasoning", "isThreat"],
                "additionalProperties": False
            }
            }
        }
        }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.status_code, "message": response.text}

# Example usage:
result = chat_with_llama3([
            {
            "role": "system",
            "content": "You are a cybersecurity analyst that detects potential cyber threats in user posts."
            },
            {
            "role": "user",
            "content": "Analyze the following post for possible new cyber threats: [Insert Post Content Here]"
            }
        ])
print(result)

