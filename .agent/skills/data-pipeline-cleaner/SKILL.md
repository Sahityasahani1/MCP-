---
name: data-pipeline-cleaner
description: Executes and validates the autonomous tabular data cleaning, outlier profiling, and algorithmic Data Health Scoring pipeline.
---

# Data Pipeline Cleaner Skill

## Overview
This skill executes the staff-level Pandas data cleaner on raw tabular datasets, calculating pre- and post-cleaning Data Health Scores (0 to 100), removing duplicates, imputing missing values, and exporting both CSV and Apache Parquet files.

## When to Use
- When testing new raw tabular datasets placed in `data/raw/`.
- When validating data health score algorithms.
- When generating clean benchmark data for model training prototypes.

## Instructions
1. Ensure the raw dataset is placed inside `data/raw/{dataset_name}/`.
2. Execute the cleaning pipeline via Python CLI:
   ```powershell
   python mcp_server/pipeline/clean_data.py --input "data/raw/{dataset_name}/{filename}.csv" --out-dir "processed_data"
   ```
3. Inspect generated artifacts in `processed_data/`:
   - `{filename}_cleaned.csv`
   - `{filename}_cleaned.parquet`
4. Verify that the output summary includes:
   - Initial Data Health Score
   - Final Data Health Score (must show non-negative delta)
   - Inferred column types and IQR outlier counts
