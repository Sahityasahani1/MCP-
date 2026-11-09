# Full Research Cycle Automation Workflow

This automation workflow details how AMRA processes an end-to-end research request from high-level prompt to clean Parquet data.

## Workflow Steps:
1. **Prompt Ingestion:** User inputs a research hypothesis via Next.js web client.
2. **Literature Survey:** Agent invokes `search_academic_papers` on arXiv with SQLite TTL caching.
3. **Dataset Sourcing:** Agent searches Kaggle for matching tabular datasets with Usability $\ge 0.70$ and Size $\le 250\text{ MB}$.
4. **HITL Gate Trigger:** Agent generates a cryptographic single-use approval token and emits `hitl_required` SSE event.
5. **User Authorization:** User reviews the cleaning recipe in the UI and clicks "Approve Pipeline".
6. **Execution & Export:** Pipeline cleans dirty CSV, calculates Data Health Scores, and exports cleaned CSV + Apache Parquet to `processed_data/`.
7. **Interactive Preview:** Frontend renders 5 preview rows and quality score delta.
