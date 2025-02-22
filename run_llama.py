

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
        "max_tokens": max_tokens
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.status_code, "message": response.text}

# Example usage:
result = chat_with_llama3([{"role": "user", "content": "Write a limerick about the wonders of GPU computing."}])
print(result)
