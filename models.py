from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = None
    predict: Optional[int] = None