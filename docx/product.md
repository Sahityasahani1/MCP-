# product.md — AMRA Product Requirements & Feature Definition

> **Project:** Autonomous ML Research Agent (AMRA)  
> **Version:** 2.0.0  
> **Status:** Production Architecture & Benchmark Approved  

---

## 1. Product Vision & Value Proposition

AMRA bridges the exploratory gap in machine learning engineering. By combining the **Model Context Protocol (MCP)** with a real-time Server-Sent Events (SSE) streaming web interface, AMRA enables practitioners to move from an abstract research idea to a cleaned, profiled tabular dataset with associated academic literature in **under 90 seconds**, operating entirely within **$0.00 free-tier cloud resources**.

---

## 2. Core Personas & Problem Scenarios

### Persona 1: Academic ML Researcher (PhD / Postdoc)
- **Goal:** Survey state-of-the-art (SOTA) literature without hallucinated citations or broken paper links.
- **Pain Points:** 
  - Hallucinated URLs and DOIs produced by conventional LLM chats.
  - Inability to quickly locate accompanying benchmark datasets.
- **AMRA Solution:** Searches the live arXiv export API, caches results in a sub-millisecond SQLite database, and returns canonical PDF links alongside paper abstracts.

### Persona 2: Applied Data Scientist / Industry ML Engineer
- **Goal:** Rapidly test feasibility and train baseline models on clean tabular data.
- **Pain Points:** 
  - Sifting through stale, empty, or multi-gigabyte Kaggle datasets.
  - Writing 30–45 minutes of manual Pandas cleaning scripts for missing values, IQR outliers, and inconsistent casing.
- **AMRA Solution:** Discovers high-usability Kaggle datasets ($> 0.70$ usability score, $< 250\text{ MB}$), triggers a secure Human-in-the-Loop approval prompt, cleans the dataset, calculates an algorithmic Data Health Score (0–100), and outputs both CSV and Apache Parquet files.

---

## 3. Comprehensive Feature Definitions

### Feature 1: Academic Literature Discovery (arXiv Tool)
- **Description:** Exposes an MCP-compliant search tool interfacing with the arXiv API.
- **Capabilities:**
  - Queries arXiv for research papers matching natural language keywords.
  - Sorts by relevance, last updated date, or submission date.
  - Filters results to return Title, Authors, Published Date, arXiv ID, Summary Abstract, and canonical PDF URL.
  - Caches responses in SQLite (`data/cache/mcp_query_cache.db`) with 24-hour TTL for $< 15\text{ ms}$ retrieval.
- **Safety Rule:** All paper links must resolve strictly to `https://arxiv.org/pdf/{arxiv_id}.pdf` and `https://arxiv.org/abs/{arxiv_id}` (BR-03 Zero Hallucination).

### Feature 2: Verified Dataset Sourcing (Kaggle Tool + Fallback)
- **Description:** Searches and inspects tabular datasets via the Kaggle API, with a guaranteed local benchmark fallback for offline operation.
- **Capabilities:**
  - Filters datasets by Usability Score ($\ge 0.70$) and maximum file size ($\le 250\text{ MB}$).
  - Inspects remote schemas without downloading the full dataset.
  - Provides a built-in verified benchmark dataset (`mlg-ulb/creditcardfraud`) for seamless local testing without Kaggle API credentials.
- **Safety Rule:** Downloads exceeding 250 MB are rejected automatically to prevent disk exhaustion.

### Feature 3: Cryptographic Human-in-the-Loop (HITL) Gate
- **Description:** A security gate that halts automated agent execution before any destructive disk modification or data transformation.
- **Capabilities:**
  - Generates a unique, single-use UUID approval token.
  - Dispatches a `hitl_required` SSE event to the client with the proposed cleaning recipe.
  - Renders an interactive `ApprovalPrompt` card in the UI detailing targeted transformations.
  - Resumes execution only upon receipt of an authorized `/api/chat/approve` payload.
  - Single-use revocation: tokens cannot be reused or replayed.

### Feature 4: Staff-Level Tabular Cleaning & Health Scoring Engine
- **Description:** An autonomous Pandas/NumPy pipeline that transforms dirty raw CSVs into production-ready analytical assets.
- **Capabilities:**
  - **Column Normalization:** Converts dirty headers to standardized `snake_case` (e.g., `"Customer Age ($)"` $\to$ `"customer_age"`).
  - **Semantic Type Inference:** Detects identifiers, continuous numerics, discrete integers, low/high cardinality categoricals, and datetimes.
  - **Missing Value Imputation:**
    - Continuous numerical features $\to$ Median imputation.
    - Categorical features $\to$ Mode imputation (with `"missing"` fallback).
    - Rows with $> 60\%$ missing values $\to$ Dropped.
  - **Deduplication:** Identifies and strips exact duplicate records.
  - **Outlier Detection:** Computes Interquartile Range (IQR) bounds ($Q_1 - 1.5 \times \text{IQR}$, $Q_3 + 1.5 \times \text{IQR}$) and logs extreme outliers.
  - **Algorithmic Data Health Scoring (0.0 to 100.0):**
    $$\text{Health Score} = 100 - (\text{Missingness Penalty} + \text{Duplicate Penalty} + \text{Outlier Penalty})$$
    Computes both Pre-Cleaning and Post-Cleaning scores to measure data quality delta.
  - **Dual Production Export:** Simultaneously generates `.csv` and `.parquet` (Apache Parquet with Snappy compression) in `/processed_data/`.

### Feature 5: Real-Time SSE Streaming & Thought Inspection
- **Description:** Low-latency Server-Sent Events stream delivering continuous feedback to the user.
- **Event Types:**
  - `thought`: Internal reasoning step (displayed in collapsible badge).
  - `tool_start`: Signals invocation of an MCP tool with arguments.
  - `tool_result`: Delivers structured tool payload.
  - `hitl_required`: Triggers user approval modal.
  - `text_delta`: Chunks of conversational text.
  - `cost_audit`: Audits token consumption and confirms free-tier usage ($0.00).
  - `complete`: Finalizes turn and updates session state.
  - `error`: Structured diagnostics if an edge failure occurs.

---

## 4. User Stories & Acceptance Criteria (Gherkin Format)

### US-01: Academic Paper Discovery
```gherkin
Feature: Academic Paper Discovery
  Scenario: Researcher queries literature on Graph Neural Networks
    Given the researcher enters "Find recent papers on graph neural networks for fraud detection"
    When the FastAPI middleware dispatches the query to the FastMCP arXiv tool
    Then the system returns between 3 and 10 verified arXiv papers
    And each paper card displays title, authors, published date, summary abstract, and canonical PDF link
    And the PDF link matches "https://arxiv.org/pdf/{arxiv_id}.pdf"
```

### US-02: Dataset Sourcing with Size Guardrails
```gherkin
Feature: Dataset Sourcing
  Scenario: Data Scientist requests a Kaggle dataset for credit card fraud
    Given the user asks for "credit card fraud detection tabular dataset"
    When the agent invokes find_kaggle_datasets
    Then the tool filters out any datasets with Usability Score < 0.70
    And the tool rejects any dataset with total size > 250 MB
    And the UI renders a DatasetCard with usability meter and file format badges
```

### US-03: Human-in-the-Loop Pipeline Authorization
```gherkin
Feature: HITL Approval Gate
  Scenario: Agent plans to clean and export a tabular dataset
    Given an ingested dataset resides in "/data/raw/"
    When the agent determines a cleaning pipeline is necessary
    Then the agent emits a "hitl_required" event with a cryptographic approval_token
    And the execution freezes without modifying files
    And an ApprovalPrompt component appears in the UI
    When the user clicks "Approve Pipeline"
    Then the frontend calls "/api/chat/approve" with the approval_token
    And the pipeline executes and writes cleaned CSV and Parquet files
```

### US-04: Data Health Scoring Integrity
```gherkin
Feature: Algorithmic Data Health Scoring
  Scenario: Evaluating dirty tabular data before and after cleaning
    Given a dataset containing missing values, duplicates, and unformatted headers
    When clean_tabular_dataset executes
    Then the pre-cleaning health score is calculated between 0.0 and 100.0
    And the post-cleaning health score is calculated between 0.0 and 100.0
    And post_score must be strictly greater than or equal to pre_score
    And both CSV and Parquet files are written to "/processed_data/"
```

---

## 5. Non-Functional Requirements (NFRs)

1. **Cost SLA:** 100% capable of running on **$0.00 operating cost** via Gemini 2.5 Flash free tier or local Ollama.
2. **Latency SLA (BR-04):**
   - Cache hit latency $< 15\text{ ms}$.
   - Data cleaning pipeline latency $< 500\text{ ms}$ for standard benchmark datasets ($\sim 1,000$ rows).
   - Time-to-First-Token (TTFT) $< 1.5\text{ s}$ over SSE stream.
3. **Security SLA (BR-05):**
   - Zero directory traversal vulnerabilities (`Path.resolve()` boundary check).
   - Zero command injection vulnerabilities (no raw shell executions).
4. **Reliability SLA (BR-02):**
   - Zero unhandled exceptions on corrupted CSV files or malformed requests; graceful fallback to `error` event.
