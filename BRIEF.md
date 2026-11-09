# BRIEF.md — Autonomous ML Research Agent (AMRA)

> **Enterprise-Grade Model Context Protocol (MCP) AI Workspace for Academic Discovery, Dataset Acquisition & Autonomous Data Cleaning**

---

## 1. Executive Summary & Vision

The **Autonomous ML Research Agent (AMRA)** is a full-stack, agentic AI platform engineered to eliminate manual friction in early-stage machine learning workflows. 

By leveraging the **Model Context Protocol (MCP)**, AMRA decouples cognitive reasoning from local execution environments. Researchers and data practitioners can input high-level research questions, discover peer-reviewed literature from arXiv, source verified Kaggle datasets, and authorize local data-cleaning pipelines—all rendered in real-time through a streaming Next.js interface with **zero operating cost ($0.00)**.

```
       ┌────────────────────────────────────────────────────────┐
       │             Autonomous ML Research Agent               │
       ├────────────────────────────────────────────────────────┤
       │  "Find 2024 papers on Graph Neural Networks for fraud  │
       │   detection, download a verified Kaggle dataset, and   │
       │   clean it for baseline modeling."                     │
       └─────────────────────────┬──────────────────────────────┘
                                 │
           ┌─────────────────────┼─────────────────────┐
           ▼                     ▼                     ▼
     [arXiv Search]      [Kaggle Sourcing]      [HITL Pipeline]
   Verified Literature    High-Usability Data   Cryptographic Gate
      Canonical PDFs      Format & Size Check   Staff Cleaning & Parquet
```

---

## 2. The Problem: Friction in Modern ML Prototyping

Modern AI researchers and data scientists spend over **70% of exploratory project time** on non-cognitive boilerplate tasks:

1. **Literature Fragmentation:**
   - Navigating fragmented web tabs across Google Scholar, arXiv, Papers With Code, and GitHub.
   - Coping with LLM hallucinations where language models invent plausible-sounding titles, non-existent authors, or broken URLs.
2. **Dataset Discovery Bottlenecks:**
   - Sifting through thousands of stale, poorly documented, or multi-gigabyte Kaggle datasets.
   - Accidentally triggering massive multi-gigabyte downloads that crash local development instances.
3. **Repetitive Data Cleaning & Profiling:**
   - Writing 30+ minutes of manual Pandas boilerplate per dataset: stripping whitespace, dropping duplicates, imputing missing values, detecting IQR outliers, and standardizing column naming to snake_case.
   - Lack of standardized, objective metrics to assess before-and-after dataset quality.
4. **Unsustainable Cloud Costs:**
   - Most existing research agents are bound exclusively to paid commercial APIs (such as Claude 3.5 Sonnet or OpenAI GPT-4o), costing $20 to $50/month in exploratory tokens—rendering them inaccessible to students, independent researchers, and budget-constrained labs.

---

## 3. The AMRA Solution

AMRA directly addresses each bottleneck through an open, decoupled, zero-cost architecture:

### 1. Decoupled Model Context Protocol (MCP)
- By exposing tools as standardized FastMCP interfaces, the reasoning LLM never directly executes arbitrary bash commands or accesses raw network sockets. All tool calls adhere to strict Pydantic schemas.

### 2. Provider-Agnostic LLM Engine ($0.00 Cost)
- Native zero-cost operation powered by:
  - **Google Gemini 2.5 Flash:** Free tier (15 RPM, 1M TPM, 1,500 requests/day) with a 1,000,000-token context window that easily ingests multi-turn dialog and tabular schemas.
  - **Groq Cloud (Llama 3.3 70B Versatile):** Ultra-high-speed inference (280–350 tokens/sec) for instantaneous responses.
  - **Ollama (Qwen 2.5 14B / Llama 3.1 8B):** 100% offline, air-gapped, zero-network private local execution.

### 3. Cryptographic Human-in-the-Loop (HITL) Security
- Destructive operations (writing files, cleaning datasets, modifying disk) require explicit user consent via single-use cryptographic approval tokens. Users inspect proposed cleaning steps before authorizing disk writes.

### 4. Staff-Level Tabular Cleaning & Health Scoring
- Calculates an algorithmic **Data Health Score (0 to 100)** evaluating missingness, duplicate density, and outlier prevalence.
- Imputes missing continuous data using medians and categoricals using modes.
- Converts column headers to uniform `snake_case`.
- Exports dual production formats: cleaned CSV and high-efficiency **Apache Parquet**.

### 5. Transparent Real-Time Streaming UI
- Built on Next.js 15 (App Router) with Server-Sent Events (SSE). Users view the model's live chain-of-thought, tool invocations, structured paper and dataset cards, and interactive 5-row preview tables.

---

## 4. Target Personas

### Persona A: Academic ML Researcher & PhD Candidate
- **Needs:** Rapid survey of peer-reviewed arXiv papers without broken links or hallucinated math.
- **AMRA Value:** Delivers canonical arXiv papers with direct PDF links in $< 2$ seconds.

### Persona B: Applied Data Scientist & ML Engineer
- **Needs:** Sourcing relevant benchmark tabular datasets, checking usability, and getting clean data ready for scikit-learn or XGBoost in minutes.
- **AMRA Value:** Slashes data discovery, download, and cleaning time from 45 minutes to under 90 seconds.

### Persona C: CS / AI Graduate Student
- **Needs:** Zero-cost access to state-of-the-art agentic workflows without needing paid API keys or enterprise cloud subscriptions.
- **AMRA Value:** Runs completely on Gemini 2.5 Flash free tier or local Ollama.

---

## 5. High-Level Technical Specifications

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Frontend** | Next.js 15, React 19, TypeScript, Tailwind CSS | Real-time chat, card rendering, HITL approval dialog |
| **Middleware** | FastAPI, Python 3.11+, Pydantic v2 | SSE streaming orchestrator, session memory |
| **Tool Execution** | FastMCP, Python stdio/async | Sandboxed paper search, Kaggle discovery, data cleaner |
| **Storage** | SQLite (WAL mode), Parquet, CSV | TTL query cache, multi-turn chat history, data lake |
| **Models** | Gemini 2.5 Flash / Groq / Ollama | Free-tier cognitive reasoning and tool dispatch |
