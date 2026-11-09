# AGENTS.md — Cross-Tool AI Agent Engineering Standards

This document defines the universal operating standards, architecture boundaries, coding conventions, and security guardrails for any AI coding assistant (Cursor, Claude Code, GitHub Copilot, Codex, Windsurf, or Antigravity) working within the **Autonomous ML Research Agent (AMRA)** codebase.

---

## 1. Project Mission & High-Level Architecture

AMRA is an enterprise-grade AI workspace designed to eliminate manual toil in early-stage machine learning workflows. It decouples high-level cognitive reasoning from local execution environments using the **Model Context Protocol (MCP)**.

### Architectural Tiers:
1. **Frontend (Presentation Tier):** Next.js 15 (App Router), TypeScript, Tailwind CSS. Consumes real-time Server-Sent Events (SSE) and renders structured cards (PaperCard, DatasetCard, ApprovalPrompt, DataPreviewTable).
2. **Middleware Host (Agent & Session Tier):** FastAPI (Python 3.11+), Pydantic v2 schemas, SQLite WAL-mode session store, provider-agnostic LLM interface (Gemini 2.5 Flash, Groq Llama 3.3 70B, Ollama Qwen 2.5 14B).
3. **Execution Layer (MCP Tools):** FastMCP server (`mcp_server/ml_research_server.py`), academic paper search (arXiv API), dataset discovery (Kaggle API + benchmark fallbacks), SQLite TTL cache (<1ms hits), and autonomous Pandas data cleaning/profiling pipeline.
4. **Data Lake (Storage Tier):** Local isolated directories: `/data/raw/` for raw ingestion and `/processed_data/` for cleaned CSV and Apache Parquet exports.

```
Next.js 15 (Frontend)
    │  ▲
    │  │ SSE Stream (/api/chat/stream, /api/chat/approve)
    ▼  │
FastAPI Middleware (/backend) ── SQLite Session Memory
    │  ▲
    │  │ Stdio / Python Tool Invocations
    ▼  │
FastMCP Server (/mcp_server) ── SQLite TTL Cache
    │
    ├── arXiv Discovery Tool
    ├── Kaggle Dataset Tool
    └── Pandas Cleaning & Health Scoring Engine (Requires HITL Approval)
```

---

## 2. Core Operational Rules for AI Agents

Every agent modifying or adding code to this repository MUST strictly abide by the following rules:

### RULE 1: Preserve Provider-Agnostic LLM Architecture ($0.00 Cost)
- AMRA operates with **zero mandatory API cost**. Default to Google Gemini 2.5 Flash (free tier: 15 RPM, 1M context) or Groq Cloud (Llama 3.3 70B) or local Ollama.
- **NEVER** introduce hardcoded dependencies on paid proprietary models (e.g., direct Anthropic Claude API calls) into the core execution path without an abstract fallback.
- Read model configuration exclusively from `backend.app.config.Settings` (`MODEL_PROVIDER`, `GEMINI_API_KEY`, `GROQ_API_KEY`, etc.).

### RULE 2: Human-in-the-Loop (HITL) Security Gating
- The agent **CANNOT** execute local disk modifications or run data-cleaning pipelines autonomously without explicit user authorization.
- When a dataset is selected for cleaning, the agent MUST emit a `hitl_required` SSE event containing:
  - `action`: `"download_and_clean"`
  - `dataset_id`: target dataset slug
  - `cleaning_recipe`: proposed transformations
  - `approval_token`: a cryptographically secure, single-use UUID token
- The pipeline executes ONLY when the frontend calls `/api/chat/approve` with that exact valid `approval_token`. Once used or rejected, the token must be invalidated.

### RULE 3: Strict Security & Path Isolation
- **Prevent Directory Traversal:** Never concatenate user-supplied strings directly into file system paths. Always sanitize file names using regex `[a-zA-Z0-9_\-\.]` and resolve paths via `Path.resolve()`. Validate that all target paths remain strictly inside `data/raw/` or `processed_data/`.
- **Prevent Command Injection:** Never use `os.system()` or `subprocess.run(shell=True)` with unsanitized parameters. Use direct Python library APIs (e.g., `kaggle.api`, `urllib`, `pandas`) or strictly parameter-split subprocess calls.
- **Limit Dataset Downloads:** Enforce a hard ceiling of 250 MB for Kaggle dataset downloads to protect local disk space and server memory. Reject datasets with Usability Score < 0.70 unless explicitly overridden.

### RULE 4: Zero Link & Citation Hallucination
- All academic literature returned to users must originate from verified queries to the official arXiv export API (`export.arxiv.org/api/query`).
- Paper links must resolve directly to canonical URLs: `https://arxiv.org/abs/{arxiv_id}` and `https://arxiv.org/pdf/{arxiv_id}.pdf`.
- Never fabricate DOI, arXiv IDs, or synthetic citation metrics.

### RULE 5: Production Benchmark Compliance (BR-01 to BR-06)
Before concluding any task or committing changes, ensure that all 6 global benchmark tests pass:
- **BR-01 (Schema Contracts & Strict Typing):** 100% Pydantic v2 validation on all API requests, responses, and SSE event schemas.
- **BR-02 (Edge Resilience & Fault Recovery):** Zero unhandled crashes on corrupted CSVs, missing columns, or invalid tokens. Graceful error event emission.
- **BR-03 (Zero Hallucination):** 100% verified arXiv and Kaggle URLs.
- **BR-04 (Latency SLA):** Cached queries return in $< 15\text{ ms}$; data cleaning pipelines on baseline datasets finish in $< 500\text{ ms}$.
- **BR-05 (Security & Path Boundaries):** Zero path traversal vulnerabilities verified by security tests.
- **BR-06 (Data Health Scoring Integrity):** Deterministic health scores bounded within $[0.0, 100.0]$ with verified score delta post-cleaning.

Run tests:
```powershell
python tests/test_phase1_production.py
python tests/test_phase2_backend.py
```

---

## 3. Technology Stack & Directory Conventions

```
MCP project/
├── backend/                  # FastAPI Middleware
│   ├── app/
│   │   ├── agent/            # Agent orchestrator, prompt definitions, SQLite session memory
│   │   ├── routers/          # /api/chat (SSE streaming & approval), /api/data (raw/clean inspection)
│   │   ├── schemas/          # Pydantic v2 models (events, requests, responses)
│   │   ├── config.py         # App settings & env loading
│   │   └── main.py           # FastAPI app entrypoint & CORS setup
│   └── requirements.txt
├── mcp_server/               # FastMCP Execution Layer
│   ├── pipeline/             # Staff-level Pandas data cleaner & health scoring engine
│   ├── tools/                # arXiv discovery tool, Kaggle search tool, SQLite TTL cache
│   ├── ml_research_server.py # FastMCP server exposing tools to agents
│   └── requirements.txt
├── frontend/                 # Next.js 15 User Interface
│   ├── app/                  # App Router (page.tsx, layout.tsx, globals.css)
│   ├── components/           # ChatInterface, PaperCard, DatasetCard, ApprovalPrompt, DataPreviewTable
│   ├── lib/                  # sse-client.ts (EventSource & fetch stream parser)
│   └── package.json
├── data/                     # Local storage (gitignored except .gitkeep)
│   ├── raw/                  # Downloaded raw datasets
│   ├── cache/                # SQLite TTL cache for search queries
│   └── sessions/             # SQLite session memory
├── processed_data/           # Output directory for cleaned CSVs and Parquet files
├── tests/                    # Production benchmark suites
├── docx/                     # Documentation hub (PRD, TRD, architecture, PDFs)
└── .agent/                   # Modular agent skills & workflows
```

---

## 4. Code Standards & Style Guide

### Python (Backend & MCP Server)
- Python Version: `3.11+`
- Typing: Comprehensive type annotations on all function signatures (`def func(arg: str) -> Dict[str, Any]:`).
- Schemas: Pydantic v2 `BaseModel` with `Field(...)` constraints and descriptions.
- Error Handling: Raise structured HTTPExceptions or yield `ErrorEvent` objects in SSE streams; never let raw stack traces leak to users.
- Logging: Structured logging via standard library `logging` or print statements formatted as `[MODULE_NAME] Action: detail`.

### TypeScript & Next.js (Frontend)
- React: Version 19 / Next.js 15 App Router (`"use client"` on interactive components).
- Typing: Strict TypeScript mode, zero `any` types; define clear interfaces for SSE events and card payloads.
- Styling: Tailwind CSS utility classes; adhere to the dark slate aesthetic (`bg-slate-900`, `text-slate-100`, `border-slate-800`).
- Stream Handling: SSE stream reader must handle chunks with buffer reconstitution to guard against fragmented JSON payloads.

---

## 5. Change Verification Workflow for Agents

Whenever creating or modifying files:
1. **Analyze:** Check impact on existing endpoints (`/api/chat/stream`, `/api/chat/approve`, `/api/health`).
2. **Implement:** Maintain modular separation between FastAPI middleware and FastMCP server.
3. **Verify:** Run both benchmark test suites:
   ```bash
   python tests/test_phase1_production.py
   python tests/test_phase2_backend.py
   ```
4. **Document:** Keep `BRIEF.md`, `product.md`, `ui.md`, `engineering.md`, and `README.md` in sync.
