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


def get_models():
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags")
        if response.status_code == 200:
            data = response.json()
            # 모델 목록에서 'name' 필드만 추출하여 리스트로 반환
            return [model["name"] for model in data.get("models", [])]
        return []
    except Exception as e:
        print(f"Ollama 모델 목록 조회 실패: {e}")
        return []