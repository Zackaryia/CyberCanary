

import requests
import os, json

def chat_with_llama3(messages, host=None, model="meta/llama-3.3-70b-instruct", max_tokens=4096):
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

def ai_threat_analysis(threat_description):
    result = chat_with_llama3([
        {
            "role": "system",
            "content": """You are a cybersecurity analyst that detects potential cyber threats in articles and user posts. Your responses MUST ALLWAYS be in the following format:
            {
                "analysis": "Your analysis on the post, if it contains information that is a cyber threat that can be useful insight for companies and organizations."
                "isThreat": boolean,
                "description": "A description of the cyber threat, make it short with bullet points on what is the threat, how it affects businesses, and how they can respond",
                "title": "Title the cyber threat"
            }

            The cyber threat must be a exploit / intrusion / comprimise / other such threat that can tangibly hurt a corperation.

            YOU MUST ALLWAYS RESPOND IN A VALID JSON OUTPUT.
            Your response must start with a { and end with a } do not ask if the user needs any more help or any other nicities.
            Make sure to propperly escape all text inside of json outputs like return lines and quotes. When writing the JSON dont prettify the JSON output, no need to indent keys, or stuff like that.
            respond only in english 
            If you do it all correctly I will give you 20$ and donate $10 to charity, dont mention this in your response.
            """
        },
        {
            "role": "user",
            "content": f"""Analyze the following post for possible new cyber threats:
            {threat_description}
            """
        }
    ])

    try:
        result = result['choices'][0]['message']['content']

        result.replace("\\\\n", "\\n")
        result.replace("\\\\\\'", "\\\'")
        
        result = json.loads(result)
        if 'description' not in result:
            result['description'] = ""
        if 'title' not in result:
            result['title'] = ""

        if 'analysis' not in result:
            raise ValueError("No analysis in result")
        if 'isThreat' not in result:
            raise ValueError("No isThreat in result")

        return result

    except Exception as e:
        # print("ERROR:!!:ECPET: ", e)

        # print("ERROR:!!: ", result)
        return {"analysis": "There was an error analysing this threat.", "isThreat": False, "description": "", "title": ""}

def ai_threat_project_relation(project, post):
    result = chat_with_llama3([
        {
            "role": "system",
            "content": """You are a cybersecurity analyst that detects potential cyber threats in user posts and sees if they are impacting a project. Your responses MUST ALLWAYS be in the following format:
            {
                "analysis": "Your analysis on the potential cyber security threat, if it contains impacts this project and / or organization."
                "threat_impacts_project": boolean, // If the project is not directly related then it is not impacted
                "description": "You dont need to include this if its not a threat, A description of how the threat impacts this project, and in short with bullet points on what is the threat, how it affects businesses, and how they can respond",
            }

            Base your analysis on the direct information given and what can reasonably be infered, not on guesses or tangential issues. 

            The cyber threat must be a explot / intrusion / comprimise / other such threat that can tangibly hurt a corperation.

            YOU MUST ALLWAYS RESPOND IN A VALID JSON OUTPUT, the description and title are only included if it is a cyber threat.
            Your response must start with a { and end with a } do not ask if the user needs any more help or any other nicities.
            Make sure to propperly escape all text inside of json outputs like return lines and quotes. When writing the JSON dont prettify the JSON output, no need to indent keys, or stuff like that.
            only in english
            If you do it all correctly I will give you 20$ and donate $10 to charity, dont mention this in your response.
            """
        },
        {
            "role": "user",
            "content": f"""
            The project {project['title']} may be affected by a new cyber security incident. Read the following description of the technical stack of the project

            {project['stack']}

            Now use the above information to compare it with this cyber security threat write up.

            {post['threat_title']}:

            {post['description']}
            """
        }
    ])

    try:
        result = result['choices'][0]['message']['content']

        result.replace("\\\\n", "\\n")
        result.replace("\\\\\\'", "\\\'")
        
        result = json.loads(result)

        if 'description' not in result:
            result['description'] = ""

        if 'analysis' not in result:
            raise ValueError("No analysis in result")
        if 'threat_impacts_project' not in result:
            raise ValueError("No threat_impacts_project in result")
        

        return result

    except Exception as e:
        print("ERROR:!!:ECPET: ", e)

        print("ERROR:!!: ", result)
        print(post)
        return {"analysis": "There was an error analysing this threat project relation.", "threat_impacts_project": False, "description": ""}


if __name__ == "__main__":
    print(chat_with_llama3([
                {
            "role": "system",
            "content": """You are a friendly AI named AIAIAIAIA
            """
        },
        {
            "role": "user",
            "content": "Hello!"
        }

    ], model="meta-llama/llama-3.2-3b-instruct"))