# Benchmark Verification Workflow

Automated workflow to audit and verify all 6 production benchmark rules for AMRA.

## Workflow Steps:
1. **Environment Check:** Ensure virtual environment dependencies are installed (`pip install -r backend/requirements.txt -r mcp_server/requirements.txt`).
2. **Execute Phase 1 Tests:** Run `python tests/test_phase1_production.py`.
   - Validates schema contracts (BR-01).
   - Validates edge resilience and error handling (BR-02).
   - Validates zero hallucination on arXiv/Kaggle links (BR-03).
   - Validates latency SLA (<15ms cache, <500ms cleaning) (BR-04).
   - Validates path traversal and security isolation (BR-05).
   - Validates health scoring math bounds (BR-06).
3. **Execute Phase 2 Tests:** Run `python tests/test_phase2_backend.py`.
   - Validates FastAPI health endpoint.
   - Validates SSE chat streaming turn.
   - Validates HITL approval flow and token validation.
4. **Report Audit Results:** Generate pass/fail summary badge.
