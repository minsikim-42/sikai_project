from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    conversation_id: int
    message: str
    model: Optional[str] = None
    predict: Optional[int] = None
    isThink: Optional[bool] = None