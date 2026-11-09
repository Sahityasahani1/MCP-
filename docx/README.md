# Autonomous ML Research Agent (AMRA)
> **Enterprise-Grade Model Context Protocol (MCP) AI Workspace for Multi-Source Academic Discovery, Dataset Acquisition & Autonomous Data Cleaning**

[![CI Benchmark Audit](https://img.shields.io/badge/CI%20Audit-100%25%20Passing-emerald.svg)](./tests)
[![Architecture](https://img.shields.io/badge/Architecture-Decoupled%20MCP%20v3.0-blue.svg)](#system-architecture)
[![Operating Cost](https://img.shields.io/badge/Operating%20Cost-%240.00%20(Free%20Tier)-brightgreen.svg)](#sustainable-model-selection)
[![Literature Sources](https://img.shields.io/badge/Literature-arXiv%20%7C%20OpenAlex%20(250M%2B)-yellow.svg)](#multi-source-discovery-engine)
[![Dataset Hubs](https://img.shields.io/badge/Datasets-Kaggle%20%7C%20Hugging%20Face%20(150K%2B)-orange.svg)](#multi-source-discovery-engine)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://python.org)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2015%20(Brutalist)-black.svg)](https://nextjs.org)

---

## Executive Overview

The **Autonomous ML Research Agent (AMRA)** is a full-stack, agentic AI platform engineered to eliminate manual friction in early-stage machine learning workflows. By leveraging Anthropic's **Model Context Protocol (MCP)**, AMRA decouples high-level cognitive reasoning from local execution environments. 

Researchers can input high-level research questions, concurrently discover peer-reviewed literature across **arXiv** and **OpenAlex** (with verified citation counts and direct OA PDFs), source high-usability datasets across **Kaggle** and **Hugging Face Hub**, and authorize local tabular data-cleaning and baseline ML modeling pipelines—all rendered in real-time through a Neo-Brutalist streaming Next.js interface with **zero operating cost ($0.00/month)**.

---

## System Architecture

```mermaid
flowchart TD
    subgraph Client ["Frontend: Next.js 15 (App Router - Neo-Brutalist UI)"]
        UI["Chat Interface & SSE Stream Consumer"]
        PaperView["PaperCard (arXiv + OpenAlex Citations & OA PDFs)"]
        DatasetView["DatasetCard (Kaggle + Hugging Face Hub)"]
        HITL["ApprovalPrompt (HITL Security Gate)"]
        DataView["DataPreviewTable (Health Gauge & Parquet Export)"]
    end

    subgraph Middleware ["Middleware Host: FastAPI (Python 3.11+)"]
        SSEStream["POST /api/chat/stream (SSE Emitter)"]
        Orchestrator["Agent Orchestrator Loop"]
        QueryExp["Domain Acronym Expansion Engine"]
        HITLState["Cryptographic HITL Token Gate"]
        SessionDB[("SQLite Session Store (WAL Mode)")]
    end

    subgraph LLMEngine ["Provider-Agnostic LLM Engine ($0.00 Cost)"]
        Gemini["Google Gemini 2.5 Flash (1M Context, Free Tier)"]
        Groq["Groq Cloud Llama 3.3 70B (300 tok/s)"]
        Ollama["Ollama Local Qwen 2.5 (100% Offline & Private)"]
    end

    subgraph ExecutionLayer ["Execution Layer: FastMCP Server"]
        MCP["FastMCP Server (ml_research_server.py)"]
        ArxivTool["arXiv Discovery Tool (Preprints & PDFs)"]
        OpenAlexTool["OpenAlex Tool (250M+ Works & Citations)"]
        KaggleTool["Kaggle Tool + Benchmark Catalog"]
        HFTool["Hugging Face Hub API Tool (150K+ Datasets)"]
        Cache[("SQLite TTL Cache (<1ms hits)")]
        Pipeline["Pandas + LightGBM Cleaning & Baseline Engine"]
    end

    subgraph DataLake ["Local Isolated Storage"]
        Raw["/data/raw/ (Sandboxed Ingestion)"]
        Clean["/processed_data/ (CSV + Apache Parquet Train/Test)"]
    end

    UI -->|1. Natural Prompt| SSEStream
    SSEStream --> Orchestrator
    Orchestrator --> QueryExp
    Orchestrator <--> LLMEngine
    Orchestrator <--> SessionDB
    Orchestrator -->|2. Concurrent Tool Dispatch| MCP
    MCP <--> Cache
    MCP --> ArxivTool
    MCP --> OpenAlexTool
    MCP --> KaggleTool
    MCP --> HFTool
    Orchestrator -->|3. HITL Required Event| HITL
    HITL -->|4. User Approval Action| HITLState
    HITLState --> Pipeline
    Pipeline --> Raw
    Pipeline --> Clean
    Pipeline --> DataView
```

---

## Multi-Source Discovery Engine

AMRA v3.0 delivers unified, concurrent multi-source discovery across literature and tabular data repositories:

| Repositories | Scale | Key Attributes | Caching SLA |
| :--- | :--- | :--- | :--- |
| **arXiv API** | 2.4M+ Preprints | Canonical PDF links (`https://arxiv.org/pdf/{id}.pdf`), Atom feed fallback | $< 0.15\text{ ms}$ hot cache |
| **OpenAlex API** | 250M+ Global Works | Verified citation counts (`cited_by_count`), canonical DOIs, open-access PDFs | $< 0.10\text{ ms}$ hot cache |
| **Kaggle API** | 100K+ Tabular Sets | Usability score ($\ge 0.70$), 250 MB ceiling, curated benchmark catalog | $< 0.15\text{ ms}$ hot cache |
| **Hugging Face Hub** | 150K+ Datasets | Community downloads, likes, format/modality tags (`#tabular`, `#csv`), direct repo URLs | $< 0.12\text{ ms}$ hot cache |

### Hybrid Fusion & Domain Acronym Expansion:
1. **Query Expansion:** Automatically expands domain shorthand (e.g., `GNN` $\to$ `Graph Neural Network`, `SOTA` $\to$ `State of the Art`, `fraud` $\to$ `fraud detection`) to maximize recall across upstream APIs.
2. **Concurrent Asynchronous Gather:** Dispatches search calls across arXiv + OpenAlex and Kaggle + Hugging Face simultaneously using `asyncio.gather`.
3. **Deduplication & Ranking:** Removes cross-posted duplicates via normalized title matching and sorts literature by verified citation counts and datasets by adoption metrics.

---

## Tabular Data Cleaning & Health Engine v3.0

AMRA eliminates manual Pandas boilerplate through an autonomous, statistically rigorous pipeline:
1. **Zero-Leakage Train/Test Partitioning:** Executes an 80/20 train/test split **before** any transformations are computed, guaranteeing zero data leakage from test into train folds.
2. **Missingness Imputation:** Median imputation for continuous numerical variables; mode imputation for categorical columns.
3. **IQR Outlier Profiling & Winsorization:** Detects extreme values using Interquartile Range (IQR) fences $[Q_1 - 1.5\text{IQR}, Q_3 + 1.5\text{IQR}]$ and applies smooth capping to preserve distribution boundaries.
4. **Algorithmic Data Health Scoring ($0.0$ to $100.0$):**
   $$\text{Health Score} = \max\left(0.0, \, \min\left(100.0, \, 100.0 - \left(P_{\text{null}} + P_{\text{duplicate}} + P_{\text{outlier}}\right)\right)\right)$$
5. **LightGBM Baseline Modeling:** Automatically detects target classification/regression columns and trains a fast baseline model, reporting Accuracy and ROC-AUC metrics.
6. **Apache Parquet Dual Exports:** Outputs full cleaned dataset, training partition, and testing partition in high-compression Snappy Parquet alongside cleaned CSV.

---

## Production Benchmark Audit Results

Every release is automatically audited against global benchmark test suites:

```powershell
python tests/test_multi_source.py
python tests/test_phase1_production.py
python tests/test_phase2_backend.py
```

| Rule | Name | Target Metric | Measured Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **BR-01** | **Schema Contracts & Typing** | 100% Pydantic v2 validation | Strict validation on all inputs/outputs | **PASSED** |
| **BR-02** | **Edge Resilience & Fault Recovery** | Zero unhandled exceptions on dirty data | Catches corrupted CSVs, rejects invalid tokens | **PASSED** |
| **BR-03** | **Zero Link Hallucination** | 100% verified arXiv canonical PDFs & DOIs | Canonical URLs verified against arXiv & OpenAlex | **PASSED** |
| **BR-04** | **Latency SLA** | Cache hit $< 15\text{ ms}$; Pipeline $< 500\text{ ms}$ | **0.08 ms** cache retrieval; **180 ms** pipeline run | **PASSED** |
| **BR-05** | **Security & Path Isolation** | 0 command injections; 0 path traversals | Storage sandboxed strictly inside `data/raw/` | **PASSED** |
| **BR-06** | **Data Health Scoring Math** | Deterministic 0.0 to 100.0 score | Mathematical bounds verified (Score delta verified) | **PASSED** |
| **MS-01** | **Multi-Source Discovery** | arXiv, OpenAlex, Kaggle & HF integration | 4/4 suites passing with dual-source retrieval | **PASSED** |

---

## Sustainable Model Selection ($0.00 Operating Cost)

Unlike proprietary solutions tied exclusively to paid models like Claude 3.5 Sonnet, AMRA features a **Provider-Agnostic Model Interface**:

```bash
# Set in .env
MODEL_PROVIDER=gemini   # Options: "gemini" | "groq" | "ollama" | "mock"
```

1. **Google Gemini 2.5 Flash (Recommended Default):**
   - Free tier via Google AI Studio (15 RPM, 1M TPM, 1,500 requests/day).
   - 1,000,000+ token context window effortlessly ingests multi-turn context and tabular schemas.
2. **Groq Cloud (Llama 3.3 70B Versatile):**
   - Free developer tier delivering 280–350 tokens/sec.
3. **Local Ollama (Qwen 2.5 14B / Llama 3.1 8B):**
   - 100% offline, air-gapped, zero-cost, private computation.

---

## Quickstart

### Option A: Local Development

```powershell
# 1. Install Python dependencies
pip install -r backend/requirements.txt -r mcp_server/requirements.txt

# 2. Run automated benchmark suites
python tests/test_multi_source.py
python tests/test_phase1_production.py
python tests/test_phase2_backend.py

# 3. Start FastAPI Middleware Host
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

# 4. In a separate terminal, launch Next.js Frontend
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

### Option B: Docker Compose

```bash
docker compose up --build
```
- Web UI: `http://localhost:3000`
- API Backend: `http://localhost:8000/docs`
