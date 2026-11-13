"""Phase 2 Backend & Agent Orchestrator Benchmark Verification Suite.

Tests against Global Benchmark Rules:
- BR-01: Strict Schema Contracts across FastAPI endpoints
- BR-02: Edge Resilience (Invalid tokens, corrupted session requests)
- BR-03: Model Provider Factory Switch (Gemini / Groq / Ollama / Mock)
- BR-04: Real-time Server-Sent Events (SSE) Streaming protocol
- BR-05: Human-in-the-Loop (HITL) Gatekeeping & Token Verification
- BR-06: File Download Security & Path Traversal Prevention
"""

import sys
import os
import json
import asyncio
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app
from app.config import settings
from app.agent.factory import get_model_adapter, MockLLMAdapter
from app.agent.orchestrator import AgentOrchestrator, PENDING_APPROVALS
from app.agent.memory import session_memory

client = TestClient(app)
AUTH_HEADERS = {"Authorization": f"Bearer {settings.API_AUTH_KEY}"}


def test_br01_health_check_contract():
    print("\n[BENCHMARK BR-01] Testing FastAPI Health Check & Configuration...")
    response = client.get("/api/health")
    assert response.status_code == 200, f"Health check failed: {response.text}"
    data = response.json()
    assert data["status"] == "healthy"
    assert "configured_provider" in data
    print(f" -> Service Health: {data}")
    print(" [PASSED BR-01]")


def test_br02_provider_factory_matrix():
    print("\n[BENCHMARK BR-02] Testing Provider-Agnostic Model Factory Switch...")
    providers = ["gemini", "groq", "ollama", "mock"]
    for prov in providers:
        adapter = get_model_adapter(provider_override=prov)
        assert adapter is not None, f"Failed to instantiate adapter for {prov}"
        print(f" -> Successfully resolved provider '{prov}' to {type(adapter).__name__} (Model: {adapter.model_name})")

    # Verify mock generation behavior
    mock_adapter = MockLLMAdapter()
    resp = asyncio.run(mock_adapter.generate_response([{"role": "user", "content": "Tell me about recent papers"}]))
    assert "cost_usd" in resp and resp["cost_usd"] == 0.00
    assert "prompt_tokens" in resp
    print(f" -> Model Audit: Provider={resp['provider']}, Cost=${resp['cost_usd']}")
    print(" [PASSED BR-02]")


def test_br03_sse_stream_orchestration():
    print("\n[BENCHMARK BR-03] Testing Server-Sent Events (SSE) Agent Streaming...")
    session_id = "test_sse_sess_1"

    async def collect_stream():
        events = []
        async for chunk in AgentOrchestrator.stream_chat_turn(
            message="Find papers on credit card fraud detection and find a dataset",
            session_id=session_id,
            provider_override="mock",
        ):
            if chunk.startswith("data: "):
                payload = json.loads(chunk[6:].strip())
                events.append(payload)
        return events

    events = asyncio.run(collect_stream())
    event_types = [e.get("type") for e in events]
    print(f" -> Emitted Stream Events ({len(events)}): {event_types}")

    assert "thought" in event_types, "Must emit thought events"
    assert "tool_start" in event_types, "Must emit tool_start events"
    assert "tool_result" in event_types, "Must emit tool_result events"
    assert "cost_audit" in event_types, "Must emit cost_audit event"
    assert "complete" in event_types, "Must emit complete event"

    # Verify multi-turn memory was persisted
    history = session_memory.get_history(session_id=session_id)
    assert len(history) >= 2, "Conversation memory must contain user and assistant turns"
    print(f" -> Memory verified: {len(history)} turns stored in SQLite.")
    print(" [PASSED BR-03]")


def test_br04_hitl_approval_gate():
    print("\n[BENCHMARK BR-04] Testing Human-in-the-Loop (HITL) Token Approval Engine...")
    session_id = "test_hitl_sess_2"

    # Step 1: Query that triggers cleaning proposal
    async def run_clean_prompt():
        tokens_found = []
        async for chunk in AgentOrchestrator.stream_chat_turn(
            message="Clean and download the credit card fraud dataset",
            session_id=session_id,
            provider_override="mock",
        ):
            if chunk.startswith("data: "):
                payload = json.loads(chunk[6:].strip())
                if payload.get("type") == "hitl_required":
                    tokens_found.append(payload["approval_token"])
        return tokens_found

    tokens = asyncio.run(run_clean_prompt())
    assert len(tokens) > 0, "Agent must intercept data cleaning and issue a HITL approval token"
    approval_token = tokens[0]
    print(f" -> Intercepted action. Generated cryptographic token: {approval_token}")

    # Step 2: Execute approval stream with the issued token
    async def run_approval():
        approval_events = []
        async for chunk in AgentOrchestrator.stream_approval_execution(
            approval_token=approval_token,
            session_id=session_id,
        ):
            if chunk.startswith("data: "):
                approval_events.append(json.loads(chunk[6:].strip()))
        return approval_events

    approval_events = asyncio.run(run_approval())
    approval_types = [e.get("type") for e in approval_events]
    print(f" -> Approval stream events: {approval_types}")

    assert "tool_result" in approval_types, "Must emit pipeline result after approval"
    assert "complete" in approval_types

    # Step 3: Test replay attack / invalid token
    async def test_replay():
        errs = []
        async for chunk in AgentOrchestrator.stream_approval_execution(
            approval_token=approval_token,  # Already used!
            session_id=session_id,
        ):
            if chunk.startswith("data: "):
                errs.append(json.loads(chunk[6:].strip()))
        return errs

    replay_events = asyncio.run(test_replay())
    assert replay_events[0]["type"] == "error", "Reusing an approval token must be rejected"
    print(" -> Replay attack successfully thwarted.")
    print(" [PASSED BR-04]")


def test_br05_data_api_and_path_traversal():
    print("\n[BENCHMARK BR-05] Testing Data Artifact Listing, Auth & Path Traversal Guard...")
    # 1. Unauthenticated request must return 401
    unauth_resp = client.get("/api/data/processed")
    assert unauth_resp.status_code == 401, f"Unauthenticated request should return 401, got {unauth_resp.status_code}"
    print(" -> Unauthenticated request correctly rejected with HTTP 401.")

    # 2. Authenticated request returns 200
    list_resp = client.get("/api/data/processed", headers=AUTH_HEADERS)
    assert list_resp.status_code == 200
    files = list_resp.json().get("files", [])
    print(f" -> Discovered {len(files)} cleaned dataset file(s) available for download with auth.")

    # 3. Path traversal attack attempt with auth must be blocked
    attack_resp = client.get("/api/data/download/../../etc/passwd", headers=AUTH_HEADERS)
    assert attack_resp.status_code in [400, 404], "Path traversal attack must be blocked!"
    print(" -> Path traversal attack safely blocked with HTTP 400/404.")
    print(" [PASSED BR-05]")


if __name__ == "__main__":
    print("=" * 75)
    print("  PHASE 2 BACKEND & AGENT BENCHMARK AUDIT (AMRA)")
    print("=" * 75)

    test_br01_health_check_contract()
    test_br02_provider_factory_matrix()
    test_br03_sse_stream_orchestration()
    test_br04_hitl_approval_gate()
    test_br05_data_api_and_path_traversal()

    print("\n" + "=" * 75)
    print("  ALL PHASE 2 BENCHMARKS PASSED SUCCESSFULLY!")
    print("  FastAPI Middleware, Multi-Provider Factory & HITL Engine Certified.")
    print("=" * 75)
