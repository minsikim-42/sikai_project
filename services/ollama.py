import json
import requests
from config import OLLAMA_URL
from models import ChatRequest
from services import tool_manager

def chat(messages: list, request: ChatRequest, callback=None):
    print("=============/chat input messages===============")
    print(json.dumps(messages, indent=2, ensure_ascii=False))
    print(f"request: {request}")
    print("====================end======================")
    
    prompt_tokens = 0
    completion_tokens = 0
    eval_time = 0
    tok_per_sec = 0
    total_duration = 0

    tool_call_count = 0
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

        full_thinking = ""
        full_content = ""
        tool_calls = None
        data = {}

        for line in response.iter_lines():
            if not line:
                continue

            data = json.loads(line)
            chunk_message = data.get("message", {})

            delta_thinking = chunk_message.get("thinking", "")
            delta_content = chunk_message.get("content", "")

            if chunk_message.get("tool_calls"):
                tool_calls = chunk_message["tool_calls"]

            full_thinking += delta_thinking
            full_content += delta_content

            # 툴콜 턴에서는 기존과 동일하게 실시간 전달을 하지 않음
            if tool_calls is None:
                if callback:
                    callback(delta_thinking, delta_content)
                else:
                    yield json.dumps({
                        "thinking": delta_thinking,
                        "content": delta_content
                    }) + "\n"

            if data.get("done"):
                break

        message = {"role": "assistant", "content": full_content}
        if tool_calls:
            message["tool_calls"] = tool_calls

        if tool_calls: # 툴 콜을 요청했다면
            tool_call_count += 1
            if tool_call_count > 2:
                messages.append({
                    "role": "system",
                    "content": "추가 검색은 하지 말고 이미 검색된 결과만으로 답변하세요."
                })
                continue
            
            messages.append(message)
            call = tool_calls[0]

            tool_name = call["function"]["name"]
            arguments = call["function"]["arguments"]
            if isinstance(arguments, str):
                arguments = json.loads(arguments)

            tool_result = tool_manager.run( # 파싱해서 해당 툴 Run
                tool_name,
                arguments
            )
            if tool_result is None:
                print("결과가 None입니다.")
                continue
            print("================tool_result==================")
            print(tool_result)
            print("====================end======================")

            content = tool_result["content"]
            if isinstance(content, (dict, list)):
                content = json.dumps(content, ensure_ascii=False)
            else:
                content = str(content)
            messages.append({
                "role": "tool",
                "tool_name": tool_name,
                "id": call["id"],
                "content": str(content)
            })
            print("=============appended messages===============")
            print(json.dumps(messages, indent=2, ensure_ascii=False))
            print("====================end======================")
            
            prompt_tokens += data.get(
                "prompt_eval_count",
                0
            )
            completion_tokens += data.get(
                "eval_count",
                0
            )
            eval_time += data.get(
                "eval_duration",
                0
            ) / 1_000_000_000
            total_duration += data.get(
                "total_duration",
                0
            ) / 1_000_000_000
            
            continue
        
        print("===================data=======================")
        print(data.get("done_reason"))
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("====================end======================")

        prompt_tokens += data.get(
            "prompt_eval_count",
            0
        )
        completion_tokens += data.get(
            "eval_count",
            0
        )
        eval_time += data.get(
            "eval_duration",
            0
        ) / 1_000_000_000
        tok_per_sec = (
            completion_tokens / eval_time
            if eval_time > 0
            else 0
        )
        total_duration += data.get(
            "total_duration",
            0
        ) / 1_000_000_000


        print(
            f"""
                =============
                Input tokens  : {prompt_tokens}
                Output tokens : {completion_tokens}
                Tokens Speed  : {tok_per_sec:.2f} tok/s
                Total duration: {total_duration:.1f}
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