"""Chat & SSE Streaming Router."""

import uuid
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from ..schemas.events import ChatRequest, ApprovalRequest
from ..agent.orchestrator import AgentOrchestrator
from ..agent.memory import session_memory

router = APIRouter(prefix="/api/chat", tags=["Chat & Agent"])


@router.post("/stream")
async def stream_chat(request: ChatRequest):
    """Initiates multi-turn SSE streaming agent reasoning."""
    session_id = request.session_id or f"sess_{uuid.uuid4().hex[:12]}"

    return StreamingResponse(
        AgentOrchestrator.stream_chat_turn(
            message=request.message,
            session_id=session_id,
            provider_override=request.provider,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Session-ID": session_id,
        },
    )


@router.post("/approve")
async def approve_pipeline(request: ApprovalRequest):
    """Executes the data pipeline after receiving HITL token authorization."""
    return StreamingResponse(
        AgentOrchestrator.stream_approval_execution(
            approval_token=request.approval_token,
            session_id=request.session_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.get("/history/{session_id}")
async def get_session_history(session_id: str):
    """Retrieves conversation history for a given session."""
    return {
        "session_id": session_id,
        "messages": session_memory.get_history(session_id=session_id, limit=50),
    }
