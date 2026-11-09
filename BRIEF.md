# BRIEF.md — Autonomous ML Research Agent (AMRA)

> **Enterprise-Grade Model Context Protocol (MCP) AI Workspace for Multi-Source Academic Discovery, Dataset Acquisition & Autonomous Data Cleaning**

---

## 1. Executive Summary & Vision

The **Autonomous ML Research Agent (AMRA)** is a full-stack, agentic AI platform engineered to eliminate manual friction in early-stage machine learning workflows. 

By leveraging the **Model Context Protocol (MCP)**, AMRA decouples cognitive reasoning from local execution environments. Researchers and data practitioners can input high-level research questions, concurrently discover peer-reviewed literature across **arXiv** and **OpenAlex** (250M+ works with citation metrics and canonical OA PDFs), source tabular datasets across **Kaggle** and **Hugging Face Hub**, and authorize local tabular data cleaning and LightGBM baseline benchmarking pipelines—all rendered in real-time through a streaming Next.js interface with **zero operating cost ($0.00/month)**.

```
       ┌────────────────────────────────────────────────────────┐
       │             Autonomous ML Research Agent               │
       ├────────────────────────────────────────────────────────┤
       │  "Find high-citation papers on Graph Neural Networks   │
       │   for fraud detection, download a verified dataset,    │
       │   and clean it for baseline modeling."                 │
       └─────────────────────────┬──────────────────────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            ▼                    ▼                    ▼
   [Literature Discovery] [Dataset Sourcing]   [HITL Execution]
    arXiv + OpenAlex (250M) Kaggle + HF Hub     Cryptographic Gate
    Verified Citation Count Formats & Usability 80/20 Leakage-Free Split
    Canonical OA PDFs & DOI Direct Repo Links   LightGBM & Parquet Export
```

---

## 2. The Problem: Friction in Modern ML Prototyping

Modern AI researchers and data scientists spend over **70% of exploratory project time** on non-cognitive boilerplate tasks:

1. **Literature Fragmentation & Citation Hallucination:**
   - Navigating fragmented web tabs across Google Scholar, arXiv, Papers With Code, and institutional repositories.
   - Sifting through LLM hallucinations where language models invent plausible-sounding titles, non-existent authors, synthetic DOIs, or broken URLs.
2. **Dataset Discovery Bottlenecks:**
   - Sifting through thousands of stale, poorly documented, or multi-gigabyte repositories on Kaggle or Hugging Face.
   - Accidentally triggering massive multi-gigabyte downloads that crash local development instances.
3. **Repetitive Data Cleaning & Preprocessing:**
   - Writing 30+ minutes of manual Pandas boilerplate per dataset: stripping whitespace, dropping duplicates, imputing missing values, detecting IQR outliers, and standardizing column naming to snake_case.
   - Risk of data leakage when preprocessing is computed across the entire dataset prior to train/test partitioning.
4. **Unsustainable Cloud Costs:**
   - Most existing research agents are bound exclusively to paid commercial APIs (such as Claude 3.5 Sonnet or OpenAI GPT-4o), costing $20 to $50/month in exploratory tokens—rendering them inaccessible to students, independent researchers, and budget-constrained labs.

---

## 3. The AMRA Solution

AMRA directly addresses each bottleneck through an open, decoupled, zero-cost architecture:

### 1. Decoupled Model Context Protocol (MCP)
- Exposes tools as standardized FastMCP interfaces. The reasoning LLM never directly executes arbitrary bash commands or accesses raw network sockets. All tool calls adhere to strict Pydantic schemas.

### 2. Multi-Source Literature Discovery (arXiv + OpenAlex)
- Concurrently queries the official arXiv export API and OpenAlex's 250M+ scholarly works graph.
- Automatically normalizes titles, filters for open-access accepted PDFs, and sorts literature by verified peer-reviewed citation counts (`cited_by_count`).

### 3. Multi-Source Dataset Sourcing (Kaggle + Hugging Face Hub)
- Concurrently searches Kaggle's public datasets and Hugging Face's 150K+ ML dataset repos.
- Enforces strict quality thresholds (usability $\ge 0.70$, download size $\le 250\text{ MB}$) with built-in benchmark catalog fallback.

### 4. Provider-Agnostic LLM Engine ($0.00 Cost)
- Native zero-cost operation powered by:
  - **Google Gemini 2.5 Flash:** Free tier (15 RPM, 1M TPM, 1,500 requests/day) with a 1,000,000-token context window that easily ingests multi-turn dialog and tabular schemas.
  - **Groq Cloud (Llama 3.3 70B Versatile):** Ultra-high-speed inference (280–350 tokens/sec) for instantaneous responses.
  - **Ollama (Qwen 2.5 14B / Llama 3.1 8B):** 100% offline, air-gapped, zero-network private local execution.

### 5. Cryptographic Human-in-the-Loop (HITL) Security
- Destructive operations (writing files, cleaning datasets, modifying disk) require explicit user consent via single-use cryptographic approval tokens. Users inspect proposed cleaning steps before authorizing disk writes.

### 6. Staff-Level Tabular Cleaning & Health Scoring v3.0
- **Zero-Leakage 80/20 Partitioning:** Splits data into train and test sets before calculating imputations.
- **IQR Outlier Winsorization:** Detects statistical outliers using Interquartile Range fences and caps extreme values.
- **Algorithmic Data Health Scoring (0 to 100):** Deterministic quality measurement based on null, duplicate, and outlier penalties.
- **LightGBM Baseline Modeling:** Generates automated baseline benchmark metrics (Accuracy, ROC-AUC).
- **Apache Parquet Dual Exports:** Produces cleaned CSV and high-efficiency Parquet partitions.

---

## 4. Key Performance Benchmarks

- **Query Latency:** Sub-1.5s Time-to-First-Token (TTFT) via Gemini 2.5 Flash / Groq Cloud.
- **Cache Hit Latency:** $< 0.15\text{ ms}$ via SQLite TTL query caching.
- **Data Cleaning Latency:** $< 500\text{ ms}$ for datasets up to 100,000 rows.
- **Operating Cost:** **$0.00 / month** (all capabilities engineered to function entirely within free quotas).
