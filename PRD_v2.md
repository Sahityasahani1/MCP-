# Product Requirements Document (PRD) v2.0
**Project:** Autonomous ML Research Agent (AMRA)  
**Version:** 2.0.0  
**Phase:** MVP & Extended Roadmap  
**Author:** AI Systems Architecture & Engineering  
**Status:** Approved / Architecture-Ready  

---

## 1. Executive Summary & Vision

The **Autonomous ML Research Agent (AMRA)** is an intelligent, developer-centric workspace designed to eliminate the friction in the exploratory phase of machine learning engineering. Currently, a researcher or data scientist must manually oscillate between literature repositories (arXiv), dataset hubs (Kaggle, Hugging Face), and local IDE environments to download, inspect, profile, and clean tabular datasets.

By leveraging the **Model Context Protocol (MCP)** and a decoupled multi-agent architecture, AMRA delivers a unified, chat-driven workspace. Researchers can query high-level hypotheses (e.g., *"Find recent 2024 papers on graph neural networks for fraud detection and download a clean benchmark dataset to test them"*), inspect verified academic papers, evaluate relevant datasets, and approve automated local data ingestion and cleaning pipelines without leaving the web interface.

---

## 2. Core Problem Statement & Key Gaps in v1.0

### Identified Gaps in v1.0 MVP:
1. **Lack of Human-in-the-Loop (HITL) Safety:** The original PRD stated *"The AI triggers a local script... once I approve it"*, but lacked functional specifications for approval tokens, interactive diff/summary cards, or destructive action safeguards.
2. **Ambiguous Data Cleaning Definition:** "Pandas cleaning" was unspecified. Datasets often fail on missing values, inconsistent data types, duplicates, and skewed formats.
3. **No Dataset Size or Quota Guardrails:** Attempting to download a multi-gigabyte Kaggle dataset would crash the local server and freeze the UI.
4. **Zero-Feedback Latency:** Academic searches and dataset downloads take 5–45 seconds. Without streaming progress indicators, users experience perceived system hangs.
5. **Vendor Lock-in & Running Cost:** Reliance on paid commercial APIs (such as Claude 3.5 Sonnet) makes widespread student and academic adoption unsustainable.

---

## 3. Target Personas & User Journeys

### Persona A: Academic ML Researcher & PhD Student
- **Need:** Rapid state-of-the-art (SOTA) literature exploration without hallucinated citations or broken paper links.
- **Pain Point:** Sifting through hundreds of arXiv preprints and struggling to find accessible datasets mentioned in paper benchmarks.

### Persona B: Applied Data Scientist & ML Engineer
- **Need:** Fast feasibility testing and baseline prototyping.
- **Pain Point:** Kaggle has thousands of stale, empty, or unformatted datasets. Downloading, inspecting headers, dropping null values, and saving takes 30+ minutes of manual boilerplate per idea.

---

## 4. User Stories & Acceptance Criteria (Gherkin Format)

### US-1: Academic Paper Discovery
* **As a** Researcher  
* **I want to** enter a natural language research query  
* **So that** the agent retrieves peer-reviewed and preprint papers with verified metadata.  
* **Acceptance Criteria:**
  - Given a search query (e.g., *"Transformers for time series forecasting"*), the agent returns between 3 to 10 verified arXiv papers.
  - Every paper entry MUST display: Title, Authors, Published Date, arXiv ID, Abstract Summary (max 120 words), and a direct PDF hyperlink.
  - Zero URL hallucinations: all links must be verified against arXiv's official export API.

### US-2: Verified Dataset Sourcing
* **As a** Data Scientist  
* **I want** the agent to recommend Kaggle datasets directly correlated with discovered papers or specified keywords  
* **So that** I don't waste time inspecting incompatible or empty repositories.  
* **Acceptance Criteria:**
  - System filters out datasets with Usability Score < 0.70 and size > 250MB (configurable for MVP).
  - Displays Dataset Slug/ID, Description, Usability Score, File formats (CSV, Parquet), Total Size, and Download Count.

### US-3: Human-in-the-Loop (HITL) Pipeline Approval
* **As a** Developer  
* **I want** the agent to present an interactive action card detailing the dataset to download and the cleaning plan before executing anything on my local disk  
* **So that** I maintain complete authority over file downloads and code execution.  
* **Acceptance Criteria:**
  - Agent presents: Target Dataset ID, File Size, Proposed Cleaning Steps (e.g., *"Handle missing values via median imputation, drop duplicates, encode timestamps"*), and Output Destination.
  - Execution strictly halts until the user clicks **"Approve & Execute"** or **"Cancel/Modify"**.

### US-4: Autonomous Ingestion, Cleaning & Profiling
* **As a** Data Scientist  
* **I want** the local execution layer to download, unzip, clean, and profile the tabular data  
* **So that** I obtain an immediate summary of the data ready for model training.  
* **Acceptance Criteria:**
  - Downloads target dataset into `/data/raw/<dataset_id>`.
  - Executes cleaning pipeline into `/processed_data/<dataset_name>_cleaned.csv`.
  - Returns a Data Health Card to the UI: Row/Column counts before vs. after, missing value resolution log, column data types, and head(5) preview.

### US-5: Real-time Streaming & Agentic Thought Visibility
* **As an** End User  
* **I want to** observe real-time thoughts and tool execution milestones  
* **So that** I know the agent is actively making progress rather than hung.  
* **Acceptance Criteria:**
  - UI renders status pills: `[Searching arXiv...]` -> `[Retrieved 5 papers]` -> `[Searching Kaggle...]` -> `[Awaiting User Confirmation]`.

---

## 5. Functional Requirements Matrix

| Module | ID | Requirement | Priority |
| :--- | :--- | :--- | :--- |
| **Chat Interface** | FR-01 | Next.js chat interface with markdown formatting, code highlights, and action cards | P0 (Must Have) |
| **Streaming UI** | FR-02 | Server-Sent Events (SSE) streaming for token-by-token text and agent status updates | P0 (Must Have) |
| **Model Agnostic** | FR-03 | Modular LLM backend supporting Free Cloud (Gemini 2.5 Flash / Groq) and Local (Ollama) | P0 (Must Have) |
| **Academic Discovery** | FR-04 | MCP tool querying arXiv API with relevance sorting and pagination | P0 (Must Have) |
| **Dataset Discovery** | FR-05 | MCP tool querying Kaggle API with size and usability filters | P0 (Must Have) |
| **HITL Confirmation** | FR-06 | Interactive UI prompt blocking subprocess execution until explicit user consent | P0 (Must Have) |
| **Data Ingestion** | FR-07 | Automated authenticated download & archive extraction with size sanity checks (<250MB) | P0 (Must Have) |
| **Data Cleaning** | FR-08 | Configurable Pandas cleaning pipeline: Null imputation, duplicate removal, standard header normalization | P0 (Must Have) |
| **Data Profiling** | FR-09 | Instant tabular preview (head, column types, shape, null counts) returned to chat | P1 (Should Have) |
| **Session Memory** | FR-10 | Multi-turn conversational memory persisted per session in SQLite/local store | P1 (Should Have) |
| **Direct File Export** | FR-11 | One-click button in UI to open or download the processed CSV from the local file system | P1 (Should Have) |

---

## 6. Non-Functional Requirements & Guardrails

1. **Performance & Latency:**
   - Time-to-First-Token (TTFT) < 1.5 seconds via streaming LLM.
   - Initial literature summary returned within 4 seconds.
   - Dataset download and cleaning completes in < 45 seconds for datasets under 100MB.
2. **Security & Guardrails:**
   - **Zero Arbitrary Code Execution:** The LLM cannot emit arbitrary shell commands. It must only pass structured parameters to strictly defined FastMCP Python tools.
   - **Path Traversal Shield:** Regex validation on dataset IDs and target output paths to prevent directory traversal attacks (`../`).
   - **Credential Sandboxing:** API keys (`KAGGLE_USERNAME`, `KAGGLE_KEY`, `GEMINI_API_KEY`) stay strictly inside backend `.env` files and are never sent to the client browser.
3. **Reliability & Sustainability:**
   - 100% free-tier operational capability with zero ongoing API licensing cost.
   - Graceful degradation: If Kaggle credentials are missing, system informs user and allows manual CSV upload or arXiv search only.

---

## 7. Success Metrics & KPIs

| Metric | Target | Measurement Method |
| :--- | :--- | :--- |
| **Time-to-Clean-Data** | < 90 seconds | From initial user prompt to cleaned CSV on disk |
| **Link Integrity** | 100% | Zero hallucinated or broken arXiv / Kaggle links |
| **Tool Calling Accuracy** | > 95% | Correct MCP tool invocation with valid JSON arguments |
| **HITL Enforcement** | 100% | 0 subprocesses executed without explicit user token approval |
| **Operating Cost** | $0.00 / month | Built exclusively on sustainable free-tier or open-weights models |

---

## 8. Four-Phase Project Delivery Roadmap

### Phase 1: Core MCP Execution Layer & Standalone Tools (The Muscle)
* **Goal:** Build and validate the FastMCP server, external API integrations, and local Pandas cleaning sandbox independently.
* **Key Deliverables:**
  - FastMCP tool server (`mcp_server/ml_research_server.py`) with stdio/async transport.
  - `search_academic_papers`: arXiv API integration with deduplication, metadata parsing, and verified PDF links.
  - `find_kaggle_datasets`: Kaggle API search with usability threshold (>0.70) and size filter (<250MB).
  - `clean_data.py`: Isolated data cleaning script (imputation, duplicate removal, header normalization, and before/after stats).
* **Exit Criteria:** FastMCP tools execute independently via CLI/inspector, returning typed JSON and saving a cleaned CSV to `/processed_data/`.

### Phase 2: Agent Orchestration, Model Integration & Streaming Middleware (The Brain)
* **Goal:** Implement the FastAPI backend, provider-agnostic LLM adapter (Gemini Flash / Groq / Ollama), and real-time SSE streaming.
* **Key Deliverables:**
  - Provider factory supporting Google Gemini 2.5 Flash (default free cloud), Groq Llama 3.3 70B, and Ollama Qwen 2.5 (local).
  - LangChain / LiteLLM agent orchestrator with semantic tool routing.
  - Human-in-the-Loop (HITL) pause-and-resume token mechanism.
  - Server-Sent Events (SSE) endpoint (`POST /api/chat/stream`) emitting thoughts, tool logs, and text deltas.
  - Multi-turn conversation memory store.
* **Exit Criteria:** API client can open an SSE stream, watch agent thoughts and tool calls in real time, and receive a HITL pause token for pipeline execution.

### Phase 3: Conversational Web Interface & Interactive Cards (The Face & Experience)
* **Goal:** Develop the Next.js 15 UI with real-time SSE streaming, responsive layout, and rich interactive components.
* **Key Deliverables:**
  - Next.js 15 App Router frontend with Tailwind CSS and Lucide icons.
  - Custom SSE stream reader (`sse-client.ts`) with live status indicators.
  - Interactive Action Cards: `PaperCard` (PDF preview), `DatasetCard` (metrics), `ApprovalPrompt` (HITL confirmation), and `DataPreviewTable` (CSV head & summary stats).
  - Direct CSV download & local file inspection trigger.
* **Exit Criteria:** Full browser-based workflow: natural language query -> live thoughts & paper cards -> dataset recommendation -> HITL approval click -> cleaned CSV displayed in UI under 90 seconds.

### Phase 4: Production Hardening, Safety Sandboxing & Multi-Model Offline Mode (The Shield & Polish)
* **Goal:** Harden security, handle failure modes, containerize with Docker, and verify 100% air-gapped local execution.
* **Key Deliverables:**
  - Subprocess execution watchdog (60s killswitch), memory caps, and path traversal protection.
  - Offline mode verification using local Ollama (`qwen2.5:14b` / `llama3.1:8b`).
  - Graceful degradation for missing API credentials or zero-result queries.
  - `docker-compose.yml` for unified one-command startup (Frontend + Backend + FastMCP).
  - Comprehensive end-to-end automated tests.
* **Exit Criteria:** Zero command injection vulnerabilities, 100% crash resilience against corrupt datasets, and seamless offline-to-cloud switching via `.env`.
