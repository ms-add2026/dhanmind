from pydantic import BaseModel
from typing import Optional


class ChatQueryRequest(BaseModel):
    message: str
    session_id: str = "default-session"


class ChatQueryResponse(BaseModel):
    answer: str
    path_used: str
    tool_result: Optional[dict] = None