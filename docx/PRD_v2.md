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
