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
import time

from fastapi import Header
from services import tool_manager, tool_planner

from services import job_manager
from threading import Thread

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

def generate_chat(
    messages,
    request,
    user_id,
    job_id
):  
    answer = ""
    thinking_process = ""

    def callback(t, c):
        nonlocal answer, thinking_process

        if t:
            thinking_process += t

        if c:
            answer += c

        job_manager.append(
            job_id,
            thinking=t,
            content=c
        )

    try:
        # callback 방식으로 실행
        for _ in ollama.chat( # ollama.chat is generator
            messages,
            request,
            callback=callback
        ):
            pass

        conversation.add_message(
            user_id,
            request.conversation_id,
            "assistant",
            answer,
            thinking_process
        )

    except Exception as e:
        print(e)

    finally:
        job_manager.finish(job_id)

    # for line in ollama.chat(messages, request, callback=callback):

    #     data = json.loads(line)

    #     if data.get("thinking"):
    #         thinking_process += data["thinking"]
    #     if data.get("content"):
    #         answer += data["content"]

    #     # 브라우저에는 그대로 전달
    #     yield line
    
    # job_manager.finish(job_id)

    # # AI 답변 저장
    # conversation.add_message(
    #     user_id,
    #     request.conversation_id,
    #     "assistant",
    #     answer,
    #     thinking_process
    # )

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


        job_id = job_manager.create_job(
            x_user_id,
            request.conversation_id
        )

        thread = Thread(
            target=generate_chat,
            args=(
                messages,
                request,
                x_user_id,
                job_id
            ),
            daemon=True
        )

        thread.start()

        return {
            "job_id": job_id
        }
        # return StreamingResponse(
        #     iter([
        #         json.dumps({
        #             "thinking": "",
        #             "content": tool_result["content"]
        #         }) + "\n"
        #     ]),
        #     media_type="text/plain"
        # )
    
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
    instruction = f"""
        Before calling search or naver_news tools, determine whether the user's question depends on the current date or time.

        If the query involves words such as:
        - today
        - now
        - current
        - latest
        - yesterday
        - tomorrow
        - this week
        - this month
        - recently

        or requires knowledge of the current date to construct an accurate search query,

        you MUST call the current_time tool first.

        Otherwise, call the search or news tool directly.
    """
    print("system prompt:", instruction)

    # 4) messages 구성 (핵심)
    messages = [
        {"role": "tool", "content": instruction},
        *remove_thinking
    ]
    


    print(f"chat request messages:\n{messages}")
    
    job_id = job_manager.create_job(
        x_user_id,
        request.conversation_id
    )
    thread = Thread(
        target=generate_chat,
        args=(
            messages,
            request,
            x_user_id,
            job_id
        ),
        daemon=True
    )

    thread.start()

    return {
        "job_id": job_id
    }
    # return StreamingResponse(
    #     generate_chat(messages, request, x_user_id),
    #     media_type="text/plain"
	# )

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

@app.get("/api/conversations") # 대화 내역들 불러오기
def list_conversations(x_user_id: str = Header("default_user")):
    return {"conversations": conversation.get_conversation_list(x_user_id)}


# 세션관리

@app.post("/conversation/new")
def new_conversation(x_user_id: str = Header("default_user")):
    print("new chat requests")
    
    info = conversation.create_conversation(x_user_id)

    return info

@app.get("/conversation/{conversation_id}")
def get_conversation(
    conversation_id:int,
    x_user_id: str = Header("default_user")
    ):

    messages = conversation.get_messages(
        x_user_id,
        conversation_id
    )

    return messages

def event_stream(job_id: str):
    last_thinking_len = 0
    last_answer_len = 0

    while True:
        job = job_manager.get_job(job_id)

        if not job:
            yield f"data: {json.dumps({'thinking': '', 'content': '', 'finished': True, 'error': 'job not found'})}\n\n"
            break

        delta_thinking = job["thinking"][last_thinking_len:]
        delta_content = job["answer"][last_answer_len:]
        last_thinking_len = len(job["thinking"])
        last_answer_len = len(job["answer"])

        if delta_thinking or delta_content or job["finished"]:
            yield f"data: {json.dumps({'thinking': delta_thinking, 'content': delta_content, 'finished': job['finished']})}\n\n"

        if job["finished"]:
            break

        time.sleep(0.1)


@app.get("/chat/stream/{job_id}")
def stream_job(job_id: str):
    return StreamingResponse(event_stream(job_id), media_type="text/event-stream")


@app.get("/chat/active/{conversation_id}")
def get_active_job(conversation_id: int, x_user_id: str = Header("default_user")):
    job_id = job_manager.get_active_job_id(x_user_id, conversation_id)
    return {"job_id": job_id}