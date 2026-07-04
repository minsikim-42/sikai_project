import json
import requests
from config import OLLAMA_URL
from models import ChatRequest

def chat(messages: list, request: ChatRequest):
    print(f"request: {request}")
    
    message = messages
    predict = request.predict or 2048
    isThink = True if request.isThink is None else request.isThink
    model = request.model or "qwen3:0.6b"

    MODEL = model #GetModel(model)
    
    response = requests.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": MODEL,
                    "messages": messages,
                    # [
                    #     {
                    #         "role": "system",
                    #         "content": instruction
                    #     },
                    #     {
                    #         "role": "user",
                    #         "content": messages
                    #     }
                    # ],
                    "think": isThink,
                    "stream": True,
                    "options": {
                        "num_ctx": 32768, # 32k
                        "num_predict": predict,
                        "temperature": 0.7,
                        "top_p": 0.9,
                    }
                },
                stream=True
            )
    
    # for line in response.iter_lines():
    #     if not line:
    #         continue

    #     data = json.loads(line)

    #     if "message" in data:
    #         yield data["message"]["content"]
            
    for line in response.iter_lines():
        if not line:
            continue

        data = json.loads(line)

        message = data.get("message", {})

        yield json.dumps({
            "thinking": message.get("thinking", ""),
            "content": message.get("content", "")
        }) + "\n"
    
    print(data["done_reason"])
