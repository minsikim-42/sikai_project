import json
import requests
from config import OLLAMA_URL
from models import ChatRequest
from services import tool_manager

def chat(messages: list, request: ChatRequest):
    print(f"request: {request}")
    
    while (True):
        message = messages
        predict = request.predict or 2048
        isThink = True if request.isThink is None else request.isThink
        model = request.model or "qwen3:0.6b"

        MODEL = model #GetModel(model)

        tools = tool_manager.get_ollama_tools()
        
        response = requests.post(
                    f"{OLLAMA_URL}/api/chat",
                    json={
                        "model": MODEL,
                        "messages": messages,
                        "tools": tools,
                        "think": isThink,
                        "stream": False,
                        "options": {
                            "num_ctx": 32768, # 32k
                            "num_predict": predict,
                            "temperature": 0.7,
                            "top_p": 0.9,
                        }
                    },
                    stream=False
                )
        
        print(json.dumps(messages, indent=2, ensure_ascii=False))
                
        # for line in response.iter_lines():
        #     if not line:
        #         continue

        #     data = json.loads(line)

        #     message = data.get("message", {})

        #     yield json.dumps({
        #         "thinking": message.get("thinking", ""),
        #         "content": message.get("content", "")
        #     }) + "\n"

        data = response.json()

        message = data["message"]
        
        tool_calls = message.get("tool_calls")

        if tool_calls: # 툴 콜을 요청했다면
            call = tool_calls[0]

            tool_name = call["function"]["name"]
            arguments = call["function"]["arguments"]
            if isinstance(arguments, str):
                arguments = json.loads(arguments)

            tool_result = tool_manager.run( # 파싱해서 해당 툴 Run
                tool_name,
                arguments
            )
            print(tool_result)

            messages.append({
                "role": "tool",
                "tool_name": tool_name,
                "id": call["id"],
                "content": json.dumps(
                    tool_result["content"],
                    ensure_ascii=False
                )
            })
            print(json.dumps(messages, indent=2, ensure_ascii=False))
            continue
        
        print(data["done_reason"])
        print(message.get("tool_calls"))
        print(json.dumps(data, indent=2, ensure_ascii=False))

        yield json.dumps({
            "thinking": message.get("thinking", ""),
            "content": message.get("content", "")
        }) + "\n"

        prompt_tokens = data.get(
            "prompt_eval_count",
            0
        )

        completion_tokens = data.get(
            "eval_count",
            0
        )


        eval_time = data.get(
            "eval_duration",
            0
        ) / 1_000_000_000


        tok_per_sec = (
            completion_tokens / eval_time
            if eval_time > 0
            else 0
        )


        print(
            f"""
        =============
        Input tokens : {prompt_tokens}
        Output tokens: {completion_tokens}
        Speed        : {tok_per_sec:.2f} tok/s
        =============
        """
        )

        break


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