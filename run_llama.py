

import requests
import os, json

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

def ai_threat_analysis(threat_info):
    result = chat_with_llama3([
        {
            "role": "system",
            "content": """You are a cybersecurity analyst that detects potential cyber threats in user posts. Your responses MUST ALLWAYS be in the following format:
            {
                "analysis": "Your analysis on the post, if it contains information that is a cyber threat that can be useful insight for companies and organizations."
                "isThreat": boolean,
                "description": "IF IT IS A CYBER THREAT then A description of the cyber threat, make it short with bullet points on what is the threat, how it affects businesses, and how they can respond",
                "title": "IF IT IS A CYBER THREAT Title the cyber threat"
            }

            YOU MUST ALLWAYS RESPOND IN A VALID JSON OUTPUT, the description and title are only included if it is a cyber threat.
            """
        },
        {
            "role": "user",
            "content": f"""Analyze the following post for possible new cyber threats:
            {threat_info}
            """
        }
    ])

    try:
        result = json.loads(result['choices'][0]['message']['content'])
        if 'description' not in result:
            result['description'] = ""
        if 'title' not in result:
            result['title'] = ""
        
        return result

    except:
        return {"analysis": "There was an error analysing this threat.", "isThreat": False, "description": "", "title": ""}


print(ai_threat_analysis("""            {"text": "the Good Samaritan. how easy to pass the person by, so sure it would make things worse. the kiddos needed another adult to step in. so grateful someone(s) did.", "created_at": "2025-02-21T04:24:27.147Z", "langs": ["en"], "tags": [], "cid": "bafyreienprbyu5thypzu3uem5s2qpt63aalmdna3j2t3lqydjiqmzsgiri", "did": "did:plc:7jjqhixxhj2vinaxr26i4gkc"}"""))

