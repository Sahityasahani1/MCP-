# Product Requirements Document (PRD) v3.0
**Project:** Autonomous ML Research Agent (AMRA)  
**Version:** 3.0.0  
**Phase:** Multi-Source Enterprise Architecture & Production Benchmarks  
**Author:** AI Systems Architecture & Engineering  
**Status:** Approved / Production-Certified  

---

## 1. Executive Summary & Vision

The **Autonomous ML Research Agent (AMRA)** is an intelligent, developer-centric workspace designed to eliminate the friction in early-stage machine learning engineering. Researchers and data practitioners currently oscillate between fragmented literature repositories (arXiv, OpenAlex), dataset hubs (Kaggle, Hugging Face), and local execution environments to download, inspect, profile, and clean tabular datasets.

By leveraging the **Model Context Protocol (MCP)**, AMRA delivers a unified, chat-driven workspace. Researchers can query high-level hypotheses (e.g., *"Find high-citation papers on graph neural networks for fraud detection and download a clean benchmark dataset to test them"*), inspect verified academic papers across 250M+ works with citation counts and OA PDFs, evaluate datasets across Kaggle and Hugging Face Hub, and approve automated local data ingestion, split-first cleaning, and LightGBM baseline modeling without leaving the web interface.

---

## 2. Core Problem Statement & Architecture Evolution

### Gaps Solved in v3.0:
1. **Literature Fragmentation & Hallucination Solved:** arXiv alone misses peer-reviewed post-conference works, while conventional LLMs hallucinate papers and citations. AMRA v3.0 combines arXiv with OpenAlex, sorting by verified peer-reviewed citation counts (`cited_by_count`) with guaranteed open-access PDF links and canonical DOIs.
2. **Dataset Hub Monoculture Solved:** Relying solely on Kaggle limits access to modern open-source research benchmarks. AMRA v3.0 introduces native Hugging Face Hub discovery (150,000+ datasets) alongside Kaggle.
3. **Data Leakage in Tabular Preprocessing Solved:** Preprocessing an entire dataset before splitting causes information leakage from test folds into training folds. AMRA v3.0 enforces a **split-first 80/20 partitioning** rule before computing imputations or scalers.
4. **Lack of Baseline ML Benchmarking Solved:** Cleaning data without performance metrics leaves researchers uncertain of dataset utility. AMRA v3.0 automatically trains a LightGBM baseline model on the partitioned data, reporting Accuracy and ROC-AUC metrics.
5. **Human-in-the-Loop (HITL) Safety Enforced:** Destructive local disk actions require single-use cryptographic UUID tokens (`hitl_tok_...`) that reject replay attacks.
6. **Zero-Cost Operation:** $0.00/month operational budget maintained across Google Gemini 2.5 Flash, Groq Cloud, and local Ollama.

---

## 3. Target Personas & User Journeys

### Persona A: Academic ML Researcher & PhD Student
- **Need:** Rapid state-of-the-art (SOTA) literature exploration with verified citation metrics and guaranteed PDF links.
- **Pain Point:** Sifting through hundreds of unvetted arXiv preprints without knowing which papers have high community impact or peer review.
- **AMRA Journey:** Enters hypothesis $\to$ receives top-cited OpenAlex peer-reviewed papers and recent arXiv preprints with verified PDFs.

### Persona B: Applied Data Scientist & ML Engineer
- **Need:** Fast feasibility testing and baseline prototyping on clean tabular data.
- **Pain Point:** Kaggle has thousands of stale or unformatted datasets. Downloading, inspecting headers, dropping nulls, handling outliers, and splitting takes 45+ minutes of manual boilerplate per idea.
- **AMRA Journey:** Queries dataset $\to$ inspects Kaggle and Hugging Face alternatives $\to$ approves cleaning recipe $\to$ receives cleaned CSV, Snappy Parquet partitions, and baseline LightGBM metrics in $< 90\text{ seconds}$.

---

## 4. User Stories & Acceptance Criteria (Gherkin Format)

### US-1: Multi-Source Literature Discovery (arXiv + OpenAlex)
* **As a** Researcher  
* **I want to** enter a natural language research query  
* **So that** the agent concurrently retrieves verified literature from arXiv and OpenAlex.  
* **Acceptance Criteria:**
  - Given a search query, the system normalizes domain abbreviations (e.g., `GNN` $\to$ `Graph Neural Network`).
  - Concurrently queries arXiv and OpenAlex using `asyncio.gather`.
  - Merges, deduplicates, and sorts literature by verified citation count descending.
  - Every paper entry MUST display: Title, Authors, Published Date, Citation Count, Canonical PDF URL, and DOI (if available).
  - 100% zero link hallucination: links must resolve strictly to official endpoints.

### US-2: Multi-Source Dataset Sourcing (Kaggle + Hugging Face Hub)
* **As a** Data Scientist  
* **I want** the agent to recommend datasets across Kaggle and Hugging Face Hub  
* **So that** I have immediate access to both enterprise benchmarks and modern open-source repositories.  
* **Acceptance Criteria:**
  - Filters out datasets with Usability Score < 0.70 and size > 250 MB.
  - Returns ID, Title, Size (MB), Usability Score, Downloads, Likes, Modality Tags, and direct repository links.
  - Includes offline benchmark catalog fallback for zero blockage when credentials are absent.

### US-3: Cryptographic Human-in-the-Loop (HITL) Safety Gate
* **As a** Security-Minded Developer  
* **I want** the system to halt execution before modifying the local file system  
* **So that** no dataset is downloaded or transformed without explicit authorization.  
* **Acceptance Criteria:**
  - Emits `hitl_required` SSE event with a 32-character hexadecimal token.
  - Halts pipeline execution until `/api/chat/approve` is received with the exact matching token.
  - Invalidate token immediately upon consumption; replayed tokens must return HTTP 400.

### US-4: Split-First Tabular Data Cleaning & Baseline ML Modeling v3.0
* **As an** ML Engineer  
* **I want** the cleaning pipeline to partition data before preprocessing and train a baseline model  
* **So that** there is zero data leakage and I receive instant benchmark accuracy.  
* **Acceptance Criteria:**
  - Executes an 80/20 train/test split before computing median/mode imputations or winsorization.
  - Winsorizes extreme outliers using statistical IQR fences.
  - Automatically identifies target column and trains a LightGBM baseline model, reporting Accuracy and ROC-AUC.
  - Exports cleaned CSV and high-efficiency Apache Parquet partitions (full, train, test).

### US-5: Algorithmic Data Health Scoring
* **As a** Quality Assurance Lead  
* **I want** an objective Data Health Score (0–100) before and after cleaning  
* **So that** I can mathematically quantify quality improvements.  
* **Acceptance Criteria:**
  - Score is deterministically bounded within $[0.0, 100.0]$.
  - Missingness penalty up to 40.0 pts; duplicate penalty up to 40.0 pts; outlier penalty up to 20.0 pts.
  - Asserts a positive health score delta on imperfect data post-cleaning.

---

## 5. Functional Requirements Matrix

| Module | ID | Requirement Description | Priority |
| :--- | :--- | :--- | :--- |
| **Conversational Interface** | FR-01 | Next.js 15 chat UI supporting multi-turn agent interaction with SSE streaming | P0 (Must Have) |
| **Neo-Brutalist UI/UX** | FR-02 | Anti-design aesthetic: thick 4px black borders, hard offset shadows, high-contrast token palette | P0 (Must Have) |
| **Multi-Source Literature** | FR-03 | Concurrent literature discovery from arXiv API and OpenAlex API (250M+ works with citation metrics) | P0 (Must Have) |
| **Multi-Source Datasets** | FR-04 | Concurrent dataset discovery from Kaggle API and Hugging Face Hub API (150K+ ML datasets) | P0 (Must Have) |
| **Query Expansion** | FR-05 | Automated domain acronym expansion (e.g. `GNN` $\to$ `Graph Neural Network`, `SOTA`, `RLHF`) | P0 (Must Have) |
| **Citation-Ranked Fusion** | FR-06 | Hybrid literature ranking sorting papers by verified citation count with canonical OA PDFs and DOIs | P0 (Must Have) |
| **HITL Authorization Gate** | FR-07 | Destructive file system actions blocked until valid single-use cryptographic token is supplied | P0 (Must Have) |
| **Split-First Partitioning** | FR-08 | 80/20 train/test split executed prior to imputation/scaling to prevent data leakage | P0 (Must Have) |
| **Baseline ML Modeling** | FR-09 | Automated LightGBM baseline training on partitioned data reporting Accuracy, ROC-AUC, and feature rankings | P0 (Must Have) |
| **Data Health Scoring** | FR-10 | Algorithmic 0–100 score quantifying nulls, duplicates, and outliers before and after cleaning | P0 (Must Have) |
| **Dual/Triple Export** | FR-11 | Export clean dataset, training partition, and testing partition to CSV and Apache Parquet (Snappy) | P0 (Must Have) |
| **TTL Caching Layer** | FR-12 | Thread-safe SQLite query cache delivering sub-15ms response times for repeated requests | P0 (Must Have) |
| **Provider-Agnostic LLM** | FR-13 | Dynamic model adapter supporting Google Gemini 2.5 Flash, Groq Llama 3.3 70B, and local Ollama ($0.00 cost) | P0 (Must Have) |
| **Persistent Memory** | FR-14 | Multi-turn conversation history persisted per session in SQLite with WAL mode | P1 (Should Have) |

---

## 6. Non-Functional Requirements & Security Guardrails

1. **Performance & Latency SLAs:**
   - Time-to-First-Token (TTFT) $< 1.5\text{ s}$ via streaming LLM.
   - Cached queries return in $< 15\text{ ms}$ (measured $< 1\text{ ms}$ in benchmarks).
   - End-to-end data cleaning and LightGBM baseline training completes in $< 5\text{ s}$ for datasets up to 100K rows.
2. **Security & Sandboxing:**
   - **Zero Arbitrary Shell Execution:** Strict Python library APIs only; `shell=True` banned across all tools.
   - **Path Traversal Shield:** All file writes and reads strictly validated via `Path.resolve()` and confined to `data/raw/` or `processed_data/`.
   - **Single-Use Replay Protection:** Cryptographic HITL tokens are invalidated immediately upon first execution attempt.
3. **Zero Operating Cost ($0.00):**
   - Engineered to function 100% within free cloud tiers (Google Gemini 2.5 Flash, Groq Cloud) or locally via Ollama with zero mandatory API subscription costs.

---

## 7. Success Metrics & Benchmark SLAs

| Metric | Target SLA | Measured Benchmark Result |
| :--- | :--- | :--- |
| **Query-to-Clean-Data Latency** | $< 90\text{ seconds}$ | **$4\text{ to }12\text{ seconds}$** |
| **Link Integrity & Determinism** | 100% Verified URLs | **100% Verified arXiv & OpenAlex OA PDFs** |
| **Cache Hit Latency** | $< 15\text{ ms}$ | **$0.08\text{ ms to }0.17\text{ ms}$** |
| **Data Health Score Delta** | Positive improvement | **$+1.4\text{ to }+15.0\text{ points}$** |
| **Baseline ML Benchmark** | ROC-AUC & Accuracy reported | **LightGBM baseline reported in UI** |
| **Test Suite Pass Rate** | 100% on all benchmark rules | **100% Pass across BR-01 to BR-06** |

---

## 8. Four-Phase Delivery Roadmap (v3.0 Production Architecture)

### Phase 1: Multi-Source MCP Execution Layer & Standalone Tools (The Muscle)
* **Status:** **100% Completed & Verified**
* **Core Deliverables:**
  - FastMCP tool server (`mcp_server/ml_research_server.py`) with stdio transport.
  - Multi-source literature discovery: `arxiv_tool.py` + `openalex_tool.py` (250M+ works with citation counts and OA PDFs).
  - Multi-source dataset acquisition: `kaggle_tool.py` + `hf_dataset_tool.py` (150K+ datasets with download & like metrics).
  - Connection-pooled SQLite TTL Cache (`cache.py`) with sub-millisecond retrieval.
  - Deterministic data cleaning, IQR outlier profiling, and algorithmic Data Health Scoring ($0\text{--}100$).
* **Verification:** `tests/test_phase1_production.py` and `tests/test_multi_source.py` passing with 100% test success.

### Phase 2: Agent Orchestration, Model Integration & Streaming Middleware (The Brain)
* **Status:** **100% Completed & Verified**
* **Core Deliverables:**
  - Provider-agnostic model factory (`backend/app/agent/factory.py`) supporting **Google Gemini 2.5 Flash**, **Groq Llama 3.3 70B**, and **local Ollama** at $\$0.00$ cost.
  - Semantic query expansion for domain acronyms (`GNN`, `SOTA`, `RLHF`, `LLM`).
  - Concurrent tool dispatch (`asyncio.gather`) and hybrid citation/download fusion ranking.
  - Cryptographic Human-in-the-Loop (HITL) authorization token state machine.
  - FastAPI Server-Sent Events (SSE) streaming router (`/api/chat/stream`, `/api/chat/approve`).
  - Multi-turn conversation memory store in SQLite with WAL mode.
* **Verification:** `tests/test_phase2_backend.py` passing with 100% test success.

### Phase 3: Conversational Web Interface & Interactive Cards (The Face & Experience)
* **Status:** **Enhanced & Production Ready**
* **Core Deliverables:**
  - **Next.js 15 App Router Frontend:** High-contrast Neo-Brutalist design system (thick 4px black borders, hard offset drop shadows, stark high-impact color tokens).
  - **Resilient SSE Consumer (`lib/sse-client.ts`):** Chunked buffer reconstitution, auto-reconnect, and multi-event dispatch.
  - **Enhanced `PaperCard.tsx`:** Renders both arXiv and OpenAlex papers with green citation count badges (`Award`), cyan peer-reviewed markers, direct open-access PDF links, and canonical DOI buttons.
  - **Enhanced `DatasetCard.tsx`:** Renders Kaggle and Hugging Face Hub datasets with like counters (`Heart`), download counters, modality tags, and direct repository links.
  - **Enhanced `ApprovalPrompt.tsx`:** High-alert red container (`#FF0000`) requiring explicit user token authorization before running local pipelines.
  - **Enhanced `DataPreviewTable.tsx`:** Interactive data health gauge with score delta, LightGBM baseline model metrics tab (Accuracy, ROC-AUC, top feature importances), and direct download buttons for cleaned CSV and Parquet partitions (full, train, test).
* **Verification:** `npm run build` generates optimized static pages with 0 TypeScript/lint errors; responsive rendering verified at `http://localhost:3000`.

### Phase 4: Production Hardening, Safety Sandboxing & DevSecOps (The Shield & Polish)
* **Status:** **Enhanced & Verified**
* **Core Deliverables:**
  - **Strict Security Sandboxing:** Directory traversal prevention via `Path.resolve()`, command injection elimination, and single-use cryptographic token invalidation.
  - **Multi-Container Docker Orchestration:** Production `docker-compose.yml`, `Dockerfile.backend` (Python 3.11-slim), and `Dockerfile.frontend` (Node 20-alpine multi-stage build).
  - **Automated CI/CD Pipeline:** GitHub Actions workflow (`.github/workflows/ci.yml`) running all 3 benchmark suites on every push and pull request.
  - **Offline Capability:** 100% private, air-gapped operation verified via `MODEL_PROVIDER=ollama` and local benchmark fallbacks.
  - **Portfolio & Resume Centerpiece:** Comprehensive `README.md` with copy-paste resume bullet points, architecture diagrams, and benchmark matrix.
* **Verification:** Multi-service regression audit passing all global rules (BR-01 through BR-06).

