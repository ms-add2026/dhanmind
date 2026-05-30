from typing import Optional

from pydantic import BaseModel


class ChatQueryRequest(BaseModel):
    message: str
    session_id: str = "default-session"


class ChatQueryResponse(BaseModel):
    answer: str
    path_used: str
    tool_result: Optional[dict] = None