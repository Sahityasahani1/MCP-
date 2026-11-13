# product.md — AMRA Product Requirements & Feature Definition

> **Project:** Autonomous ML Research Agent (AMRA)  
> **Version:** 3.0.0  
> **Status:** Production Architecture & Benchmark Approved  

---

## 1. Product Vision & Value Proposition

AMRA bridges the exploratory gap in machine learning engineering. By combining the **Model Context Protocol (MCP)** with a real-time Server-Sent Events (SSE) streaming web interface, AMRA enables practitioners to move from an abstract research hypothesis to verified academic literature, sourced datasets across multiple repositories, and a cleaned, partitioned, and benchmarked tabular dataset in **under 90 seconds**, operating entirely within **$0.00 free-tier cloud resources**.

---

## 2. Core Personas & Problem Scenarios

### Persona 1: Academic ML Researcher (PhD / Postdoc)
- **Goal:** Survey state-of-the-art (SOTA) literature without hallucinated citations or broken paper links.
- **Pain Points:** 
  - Hallucinated URLs and DOIs produced by conventional LLM chats.
  - Inability to quickly locate accompanying benchmark datasets.
- **AMRA Solution:** Searches the live arXiv export API and OpenAlex's 250M+ scholarly works graph, caches results in a sub-millisecond SQLite database, and returns canonical PDF links, verified citation counts, and DOIs.

### Persona 2: Applied Data Scientist / Industry ML Engineer
- **Goal:** Rapidly test feasibility and train baseline models on clean tabular data.
- **Pain Points:** 
  - Sifting through stale, empty, or multi-gigabyte Kaggle and Hugging Face datasets.
  - Writing 30–45 minutes of manual Pandas cleaning scripts for missing values, IQR outliers, and inconsistent casing.
  - Risk of data leakage during exploratory preprocessing.
- **AMRA Solution:** Discovers high-usability datasets across Kaggle and Hugging Face Hub, triggers a secure Human-in-the-Loop approval prompt, cleans the dataset with split-first zero leakage, trains a LightGBM baseline model, calculates an algorithmic Data Health Score (0–100), and outputs both CSV and Apache Parquet files.

---

## 3. Comprehensive Feature Definitions

### Feature 1: Multi-Source Literature Discovery (arXiv + OpenAlex)
- **Description:** Exposes MCP-compliant tools interfacing with the official arXiv export API and the OpenAlex scholarly graph.
- **Capabilities:**
  - Queries arXiv and OpenAlex concurrently using domain acronym expansion (`GNN` $\to$ `Graph Neural Network`).
  - Sorts papers by verified peer-reviewed citation counts (`cited_by_count`).
  - Filters results to return Title, Authors, Published Date, Abstract Summary, canonical OA PDF URL, and DOI.
  - Caches responses in SQLite (`data/cache/mcp_query_cache.db`) with 24-hour TTL for $< 15\text{ ms}$ retrieval.
- **Safety Rule:** All paper links must resolve strictly to `https://arxiv.org/pdf/{arxiv_id}.pdf` or verified open-access publisher locations (BR-03 Zero Hallucination).

### Feature 2: Multi-Source Dataset Sourcing (Kaggle + Hugging Face Hub)
- **Description:** Searches and inspects tabular datasets across Kaggle and Hugging Face Hub, with a guaranteed local benchmark fallback for offline operation.
- **Capabilities:**
  - Filters datasets by Usability Score ($\ge 0.70$) and maximum file size ($\le 250\text{ MB}$).
  - Extracts community downloads, likes, and format/modality tags (`#tabular`, `#csv`).
  - Inspects remote schemas without downloading full archives.
  - Curated benchmark catalog fallback ensures zero pipeline blockage when credentials are not configured.
- **Safety Rule:** Downloads exceeding 250 MB are rejected automatically to prevent disk exhaustion.

### Feature 3: Cryptographic Human-in-the-Loop (HITL) Gate
- **Description:** A security gate that halts automated agent execution before any destructive disk modification or data transformation.
- **Capabilities:**
  - Generates a unique, single-use UUID approval token.
  - Dispatches a `hitl_required` SSE event to the client with the proposed cleaning recipe.
  - Renders an interactive `ApprovalPrompt` card in the UI detailing targeted transformations.
  - Resumes execution only upon receipt of an authorized `/api/chat/approve` payload.
  - Single-use revocation: tokens cannot be reused or replayed.

### Feature 4: Staff-Level Tabular Cleaning & Baseline ML Engine v3.0
- **Description:** Autonomous data cleaning, statistical profiling, and baseline machine learning pipeline.
- **Capabilities:**
  - **Zero-Leakage 80/20 Partitioning:** Splits dataset into train and test sets before computing imputations or scalers.
  - **Missingness Imputation:** Median imputation for continuous variables; mode imputation for categorical columns.
  - **IQR Outlier Winsorization:** Detects statistical outliers using Interquartile Range fences $[Q_1 - 1.5\text{IQR}, Q_3 + 1.5\text{IQR}]$ and caps extreme values.
  - **Header Normalization:** Converts column headers to uniform `snake_case`.
  - **Baseline ML Benchmark:** Automatically detects target columns, encodes features, and trains a fast LightGBM baseline model, reporting Accuracy and ROC-AUC metrics.
  - **Dual Production Export:** Cleaned CSV and high-efficiency Apache Parquet partitions (full, train, test).

### Feature 5: Algorithmic Data Health Scoring
- **Description:** Deterministic mathematical assessment of tabular dataset quality before and after cleaning.
- **Formula:**
  $$\text{Health Score} = \max\left(0.0, \, \min\left(100.0, \, 100.0 - \left(P_{\text{null}} + P_{\text{duplicate}} + P_{\text{outlier}}\right)\right)\right)$$
- **Penalties:**
  - Null Cell Penalty: Up to 40.0 points based on missing cell proportion.
  - Duplicate Row Penalty: Up to 40.0 points based on duplicate row ratio.
  - Outlier Penalty: Up to 20.0 points based on IQR outlier cell ratio.

### Feature 6: Sustainable Provider-Agnostic LLM Engine ($0.00 Cost)
- **Description:** Decoupled model adapter supporting Google Gemini 2.5 Flash (default), Groq Cloud (Llama 3.3 70B), and local Ollama (Qwen 2.5 14B).
- **Audit:** Emits real-time `cost_audit` SSE events verifying token counts and $0.00 expenditure.

### Feature 7: Neo-Brutalist Presentation Tier (Next.js 15)
- **Description:** Raw, stark, high-contrast user interface engineered for clarity and cognitive efficiency.
- **Design Rules:** 0px border radius, 4px solid black borders, hard offset box-shadows, default system fonts, instant state changes, and 100% WCAG AA contrast compliance.

### Feature 8: Custom Tabular CSV Ingestion & Interactive HITL Recipe Customizer
- **Description:** Enables researchers to upload local CSV files (up to 250 MB ceiling) directly into AMRA via drag-and-drop modal, receive instantaneous schema previews, and adjust train/test split partitions, missing value imputation rules, and target prediction features before authorizing execution.

### Feature 9: Academic Research Dossier & Canonical BibTeX Reference Export
- **Description:** Generates 1-click downloadable research reports in academic Markdown (`.md`) and standard BibTeX reference blocks (`.bib`), ready for direct import into LaTeX and Overleaf manuscripts.

### Feature 10: Multi-Tenant Authentication & Persistent User History Database
- **Description:** Complete user authentication and thread isolation engine backed by persistent SQLite WAL mode database (`data/sessions/amra_users.db`).
- **Capabilities:**
  - **NIST PBKDF2 Password Security:** PBKDF2-HMAC-SHA256 with 100,000 iterations and per-user salt for local accounts.
  - **PyJWT Session Management:** Cryptographically signed access tokens with 7-day expiration.
  - **Multi-Provider Social Sign-In:** Production OAuth 2.0 flows for **Google (Gmail)**, **GitHub**, and **Microsoft (Outlook)**.
  - **Developer Sandbox Mock Identities:** 1-click test identities for Google, GitHub, and Outlook that work immediately without external cloud configuration.
  - **Multi-Tenant History Isolation:** Complete database-level isolation of user sessions and research messages by `user_id`.
  - **Neo-Brutalist Auth Portal:** Dedicated `/login` page with tabbed Sign In/Sign Up forms, social authentication buttons, and dynamic header user profile pill with logout.

### Feature 11: Cloudflare Pages Deployment & Multi-Tier Load-Mitigation Caching
- **Description:** Edge deployment readiness on Cloudflare Pages paired with a 3-tier caching topology designed to sustain extreme traffic spikes, eliminate redundant upstream API calls, and deliver sub-millisecond responses.
- **Capabilities:**
  - **Tier 1: Cloudflare Global Edge CDN:** Deployed with `public/_headers` and `public/_routes.json` distributing static Next.js assets across 330+ edge PoPs with 1-year immutable caching (`max-age=31536000`), edge stale-while-revalidate, and Cloudflare DDoS shield.
  - **Tier 2: In-Memory RAM Edge Cache:** High-concurrency thread-safe LRU/TTL cache in FastAPI (`backend/app/cache.py`) delivering $< 0.01\text{ ms}$ cached responses at $> 40,000\text{ RPS}$ under heavy burst traffic.
  - **Tier 3: Multi-Source SQLite Query Cache:** Persistent disk cache (`data/cache/mcp_query_cache.db`) preserving literature and dataset discovery results across restarts with 24-hour retention.
  - **Cloudflare Edge Dashboard (`/cloudflare`):** Real-time interactive dashboard featuring live cache telemetry (hit ratio %, saved compute latency, active entries), an interactive high-concurrency load burst benchmark simulator, live HTTP response header inspection (`CF-Cache-Status`, `CDN-Cache-Control`, `X-Cache`), and 1-click cache purge controls.
