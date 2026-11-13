"""Chat & SSE Streaming Router with Multi-Tenant User Isolation."""

import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from ..schemas.events import ChatRequest, ApprovalRequest
from ..agent.orchestrator import AgentOrchestrator
from ..agent.memory import session_memory
from ..auth import get_current_user

router = APIRouter(prefix="/api/chat", tags=["Chat & Agent"])


@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Initiates multi-turn SSE streaming agent reasoning isolated by authenticated user."""
    session_id = request.session_id or f"sess_{uuid.uuid4().hex[:12]}"
    user_id = current_user.get("id", "usr_default_dev")

    return StreamingResponse(
        AgentOrchestrator.stream_chat_turn(
            message=request.message,
            session_id=session_id,
            provider_override=request.provider,
            user_id=user_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Session-ID": session_id,
        },
    )


@router.post("/approve")
async def approve_pipeline(
    request: ApprovalRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Executes or rejects the data pipeline after receiving HITL token authorization."""
    return StreamingResponse(
        AgentOrchestrator.stream_approval_execution(
            approval_token=request.approval_token,
            session_id=request.session_id,
            action=request.action,
            custom_recipe=request.custom_recipe,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.get("/sessions")
async def list_sessions(
    limit: int = 30,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Lists historical chat sessions from SQLite store strictly isolated by current user."""
    user_id = current_user.get("id", "usr_default_dev")
    return {
        "sessions": session_memory.list_sessions(user_id=user_id, limit=limit),
    }


@router.get("/history/{session_id}")
async def get_session_history(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Retrieves conversation history for a given session belonging to the current user."""
    user_id = current_user.get("id", "usr_default_dev")
    return {
        "session_id": session_id,
        "messages": session_memory.get_history(session_id=session_id, user_id=user_id, limit=50),
    }
