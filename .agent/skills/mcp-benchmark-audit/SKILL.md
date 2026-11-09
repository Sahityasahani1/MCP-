---
name: mcp-benchmark-audit
description: Executes and validates the 6 core production benchmark rules (BR-01 through BR-06) for the Autonomous ML Research Agent.
---

# MCP Benchmark Audit Skill

## Overview
This skill executes the automated benchmark audit for AMRA to verify schema contracts, fault tolerance, zero hallucination, latency SLAs, path isolation security, and data health mathematical bounds.

## When to Use
- Before pushing any commit or merging PRs.
- After modifying FastMCP tools (`mcp_server/tools/`).
- After updating the Pandas data cleaning pipeline (`mcp_server/pipeline/clean_data.py`).
- After updating FastAPI routes or Pydantic event schemas.

## Instructions
1. Run Phase 1 MCP Production Benchmarks:
   ```powershell
   python tests/test_phase1_production.py
   ```
2. Run Phase 2 Backend & SSE Streaming Benchmarks:
   ```powershell
   python tests/test_phase2_backend.py
   ```
3. Verify that all 6 benchmark rules pass:
   - **BR-01**: Schema contracts and strict typing
   - **BR-02**: Edge resilience on dirty/corrupted data
   - **BR-03**: Zero hallucination on arXiv/Kaggle URLs
   - **BR-04**: Latency SLA (cache $<15\text{ms}$, cleaning $<500\text{ms}$)
   - **BR-05**: Security & path traversal isolation
   - **BR-06**: Data health math bounding ($0.0 - 100.0$)
