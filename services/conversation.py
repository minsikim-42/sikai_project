import json
import os
from datetime import datetime

DATA_PATH = "data/conversations"

os.makedirs(DATA_PATH, exist_ok=True)

def create_conversation():
    folders = os.listdir(DATA_PATH)

    numbers = []
    for folder in folders:
        numbers.append(int(folder))
    if len(numbers) == 0:
        conversation_id = 1
    else:
        conversation_id = max(numbers) + 1
    
    path = f"{DATA_PATH}/{conversation_id}"
    os.mkdir(path)
    
    info = {
        "id": conversation_id,
        "title": "새 대화",
        "created_at": datetime.now().isoformat()
    }
    messages = []

    with open(f"{path}/info.json", "w", encoding="utf-8") as f:
        json.dump(info, f)
    with open(f"{path}/messages.json", "w", encoding="utf-8") as f:
        json.dump(messages, f)
    
    return conversation_id

def ensure_conversation(conversation_id):
    path = f"{DATA_PATH}/{conversation_id}"

    if os.path.exists(path):
        return

    os.mkdir(path)

    info = {
        "id": conversation_id,
        "title": f"Conversation {conversation_id}",
        "created_at": datetime.now().isoformat()
    }

    with open(f"{path}/info.json", "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=4)

    with open(f"{path}/messages.json", "w", encoding="utf-8") as f:
        json.dump([], f)

def add_message(conversation_id, role, content):

    path = f"{DATA_PATH}/{conversation_id}/messages.json"

    with open(path, "r", encoding="utf-8") as f:
        messages = json.load(f)

    messages.append({
        "role": role,
        "content": content
    })

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            messages,
            f,
            ensure_ascii=False,
            indent=4
        )

def get_messages(conversation_id):
    path = f"{DATA_PATH}/{conversation_id}/messages.json"

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)