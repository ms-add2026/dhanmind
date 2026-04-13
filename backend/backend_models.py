from pydantic import BaseModel
from typing import Optional


class ChatQueryRequest(BaseModel):
    message: str


class ChatQueryResponse(BaseModel):
    answer: str
    path_used: str
    tool_result: Optional[dict] = None