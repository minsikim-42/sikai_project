import json
import requests
from config import OLLAMA_URL
from models import ChatRequest

def chat(request: ChatRequest):
    message = request.message
    predict = request.predict or 2048
    model = request.model or "qwen3:0.6b"

    print(f"request: {request}")

    MODEL = model #GetModel(model)
    instruction = "한글을 기본언어로 한다. 짧게 대답한다."
    response = requests.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": instruction
                        },
                        {
                            "role": "user",
                            "content": message
                        }
                    ],
                    "stream": True,
                    "options": {
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
