# Autonomous ML Research Agent (AMRA)

An intelligent, Model Context Protocol (MCP) powered workspace that automates academic literature discovery (arXiv), dataset acquisition (Kaggle), and local tabular data cleaning (Pandas).

---

## Architecture & Documentation

- [**`PRD_v2.md`**](./PRD_v2.md) — Product Requirements Document (v2.0)
- [**`TRD_v2.md`**](./TRD_v2.md) — Technical Requirements Document (v2.0)
- [**`.env.example`**](./.env.example) — Environment configuration template

---

## 4-Phase Implementation Status

- [x] **Phase 1: Core MCP Execution Layer & Standalone Tools** *(Completed & Verified)*
  - `mcp_server/ml_research_server.py`: FastMCP server registering strictly typed tools.
  - `mcp_server/tools/arxiv_tool.py`: arXiv academic search with direct PDF URL extraction.
  - `mcp_server/tools/kaggle_tool.py`: Kaggle dataset discovery with usability/size filters and benchmark fallback.
  - `mcp_server/pipeline/clean_data.py`: Deterministic Pandas cleaning and data health profiling.
  - `mcp_server/test_phase1.py`: Automated verification suite.
- [ ] **Phase 2: Agent Orchestration & SSE Middleware** *(Next)*
- [ ] **Phase 3: Conversational Web Interface (Next.js 15)**
- [ ] **Phase 4: Production Hardening, Sandbox Security & Offline Mode**

---

## Quickstart: Verifying Phase 1 Tools

```bash
# Run the Phase 1 test suite
python mcp_server/test_phase1.py
```
