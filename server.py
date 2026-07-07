from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from services import ollama
from models import ChatRequest

from fastapi import Depends
from security import verify_api_key

from slowapi import Limiter
from slowapi.util import get_remote_address

from services import conversation
import json

from fastapi import Header
from services import tool_manager, tool_planner

limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter

# HTML/CSS/JS 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
# @limiter.limit("20/minute")
def home(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {}
    )

@app.get("/chat")
# @limiter.limit("20/minute")
def chatHome(
    request: Request,
    _: None = Depends(verify_api_key)
):
    return templates.TemplateResponse(
        request,
        "chat.html",
        {}
    )

def stream_chat(messages: list, request: ChatRequest, user_id: str):
    answer = ""
    thinking_process = ""

    for line in ollama.chat(messages, request):

        data = json.loads(line)

        if data.get("thinking"):
            thinking_process += data["thinking"]
        if data.get("content"):
            answer += data["content"]

        # 브라우저에는 그대로 전달
        yield line

    # AI 답변 저장
    conversation.add_message(
        user_id,
        request.conversation_id,
        "assistant",
        answer,
        thinking_process
    )

@app.post("/chat")
# @limiter.limit("10/minute")
def chat(
    request: ChatRequest,
    x_user_id: str = Header("default_user"),
    _: None = Depends(verify_api_key)
):
    plan = tool_planner.plan(request.message)
    tool_result = None
    if plan["use_tool"]:
        tool_result = tool_manager.run(
            plan["tool"],
            plan["argument"]
        )

    if tool_result is not None:
        conversation.ensure_conversation(
            x_user_id,
            request.conversation_id
        )
        conversation.add_message(
            x_user_id,
            request.conversation_id,
            "user",
            request.message
        )
        # Tool 결과를 assistant처럼 저장
        conversation.add_message(
            x_user_id,
            request.conversation_id,
            "assistant",
            tool_result["content"]
        )

        return StreamingResponse(
            iter([
                json.dumps({
                    "thinking": "",
                    "content": tool_result["content"]
                }) + "\n"
            ]),
            media_type="text/plain"
        )
    
    conversation.ensure_conversation(x_user_id, request.conversation_id)
    conversation.add_message(
        x_user_id,
        request.conversation_id,
        "user",
        request.message
    )
    
    # 2) history 가져오기
    history = conversation.get_messages(x_user_id, request.conversation_id)

    remove_thinking = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in history
            if "content" in msg
    ]

    # 3) system prompt
    instruction = "Answer briefly."

    # 4) messages 구성 (핵심)
    messages = [
        {"role": "system", "content": instruction},
        *remove_thinking
    ]
    
    print(f"chat request messages:\n{messages}")
    
    return StreamingResponse(
        stream_chat(history, request, x_user_id),
        media_type="text/plain"
	)

@app.get("/chat/{conversation_id}/messages")
def get_conversation_messages(conversation_id: int, x_user_id: str = Header("default_user")):
    print(f"👉 [조회 요청] 접속자 ID: {x_user_id} / 대화방: {conversation_id}")
    conversation.ensure_conversation(x_user_id, conversation_id)
    messages = conversation.get_messages(x_user_id, conversation_id)
    print(messages)
    return {"messages": messages}

@app.get("/api/models")
def list_models(request: Request, _: None = Depends(verify_api_key)):
    models = ollama.get_models()
    return {"models": models}

@app.get("/api/conversations")
def list_conversations(x_user_id: str = Header("default_user")):
    return {"conversations": conversation.get_conversation_list(x_user_id)}

@app.post("/api/conversations")
def new_conversation(x_user_id: str = Header("default_user")):
    new_id = conversation.create_conversation(x_user_id)
    return {"id": new_id}