from fastapi import APIRouter, HTTPException
from backend_models import ChatQueryRequest, ChatQueryResponse
from agent.graph import run_agent

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/health")
def health():
    return {"status": "ok", "service": "DhanMind Chat Service"}


@router.post("/", response_model=ChatQueryResponse)
async def process_user_query(request: ChatQueryRequest):
    try:
        result = await run_agent(request.message, request.session_id)
        return ChatQueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))