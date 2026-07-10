import json
import os
from datetime import datetime

DATA_PATH = "data/users"

os.makedirs(DATA_PATH, exist_ok=True)

# 💡 특정 유저의 대화 폴더 경로를 반환하는 헬퍼 함수
def get_user_path(user_id: str):
    user_dir = f"{DATA_PATH}/{user_id}/conversations"
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def create_conversation(user_id: str):
    user_path = get_user_path(user_id)
    folders = os.listdir(user_path)

    numbers = []
    for folder in folders:
        numbers.append(int(folder))
    if len(numbers) == 0:
        conversation_id = 1
    else:
        conversation_id = max(numbers) + 1
    
    path = f"{user_path}/{conversation_id}"
    os.makedirs(path, exist_ok=True)
    
    info = {
        "id": conversation_id,
        "title": f"대화 {conversation_id}",
        "created_at": datetime.now().isoformat()
    }
    messages = []

    with open(f"{path}/info.json", "w", encoding="utf-8") as f:
        json.dump(info, f)
    with open(f"{path}/messages.json", "w", encoding="utf-8") as f:
        json.dump(messages, f)
    
    return info

def ensure_conversation(user_id: str, conversation_id: int):
    path = get_user_path(user_id)
    conv_path = f"{path}/{conversation_id}"

    # 💡 1) 폴더가 없으면 일단 무조건 만듭니다.
    os.makedirs(conv_path, exist_ok=True)

    info_file = f"{conv_path}/info.json"
    msg_file = f"{conv_path}/messages.json"

    # 💡 2) 폴더가 있더라도 info.json 파일이 실제로 없으면 새로 만듭니다.
    if not os.path.exists(info_file):
        info = {
            "id": conversation_id,
            "title": f"Conversation {conversation_id}",
            "created_at": datetime.now().isoformat()
        }
        with open(info_file, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=4)

    # 💡 3) 폴더가 있더라도 messages.json 파일이 실제로 없으면 새로 만듭니다! (에러 해결 핵심)
    if not os.path.exists(msg_file):
        with open(msg_file, "w", encoding="utf-8") as f:
            json.dump([], f)


def add_message(user_id: str, conversation_id: int, role: str, content: str, thinking: str = ""):
    # 💡 만약을 대비해 add_message 실행 직전에도 파일이 확실히 있는지 한 번 더 보장해 줍니다!
    ensure_conversation(user_id, conversation_id)

    file_path = f"{get_user_path(user_id)}/{conversation_id}/messages.json"

    with open(file_path, "r", encoding="utf-8") as f:
        messages = json.load(f)

    msg_data = {"role": role, "content": content}
    if thinking:
        msg_data["thinking"] = thinking

    messages.append(msg_data)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=4)

def get_messages(user_id: str, conversation_id):
    user_path = get_user_path(user_id)
    path = f"{user_path}/{conversation_id}/messages.json"

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
def get_conversation_list(user_id: str):
    path = get_user_path(user_id)
    folders = os.listdir(path)
    conv_list = []
    
    for folder in folders:
        info_path = f"{path}/{folder}/info.json"
        if os.path.exists(info_path):
            with open(info_path, "r", encoding="utf-8") as f:
                conv_list.append(json.load(f))
                
    conv_list.sort(key=lambda x: x["id"], reverse=True)
    return conv_list
