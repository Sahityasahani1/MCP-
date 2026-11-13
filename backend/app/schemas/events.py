"""Pydantic Event Schemas for Server-Sent Events (SSE) Streaming Protocol."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
import time


class StreamEvent(BaseModel):
    """Base event model."""
    timestamp: float = Field(default_factory=time.time)


class ThoughtEvent(StreamEvent):
    type: Literal["thought"] = "thought"
    content: str


class ToolStartEvent(StreamEvent):
    type: Literal["tool_start"] = "tool_start"
    tool: str
    args: Dict[str, Any]


class ToolResultEvent(StreamEvent):
    type: Literal["tool_result"] = "tool_result"
    tool: str
    result: Any


class HITLRequiredEvent(StreamEvent):
    type: Literal["hitl_required"] = "hitl_required"
    action: str = "download_and_clean"
    dataset_id: str
    cleaning_recipe: Dict[str, Any]
    approval_token: str
    message: str = "Pipeline execution requires user authorization before modifying local disk."


class TextDeltaEvent(StreamEvent):
    type: Literal["text_delta"] = "text_delta"
    content: str


class CostAuditEvent(StreamEvent):
    type: Literal["cost_audit"] = "cost_audit"
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float = 0.00
    is_free_tier: bool = True


class CompleteEvent(StreamEvent):
    type: Literal["complete"] = "complete"
    session_id: str


class ErrorEvent(StreamEvent):
    type: Literal["error"] = "error"
    error_message: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: Optional[str] = None
    provider: Optional[str] = None  # "gemini" | "groq" | "ollama"


class ApprovalRequest(BaseModel):
    approval_token: str
    session_id: str
    action: Literal["approve", "reject"] = "approve"
    custom_recipe: Optional[Dict[str, Any]] = None
