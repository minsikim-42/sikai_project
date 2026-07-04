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


@app.post("/chat")
# @limiter.limit("10/minute")
def chat(
    request: ChatRequest,
    _: None = Depends(verify_api_key)
):
    conversation.ensure_conversation(request.conversation_id)

    conversation.add_message(
        request.conversation_id,
        "user",
        request.message
    )
    
    # 2) history 가져오기
    history = conversation.get_messages(request.conversation_id)

    # 3) system prompt
    instruction = "한글을 기본으로 하고 짧게 답변한다."

    # 4) messages 구성 (핵심)
    messages = [
        {"role": "system", "content": instruction},
        *history
    ]
    
    print(messages)
    
    return StreamingResponse(
        stream_chat(history, request),
        media_type="text/plain"
	)

def stream_chat(messages: list, request: ChatRequest):
    answer = ""

    for line in ollama.chat(messages, request):

        data = json.loads(line)

        if data["content"]:
            answer += data["content"]

        # 브라우저에는 그대로 전달
        yield line

    # AI 답변 저장
    conversation.add_message(
        request.conversation_id,
        "assistant",
        answer
    )