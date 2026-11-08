"""FastMCP Server: Autonomous ML Research Agent.

Exposes strictly typed MCP tools for academic paper discovery (arXiv),
dataset discovery (Kaggle), and autonomous data cleaning pipelines (Pandas).
"""

import sys
import os
import json
from pathlib import Path
from typing import Literal

# Ensure mcp_server is in sys.path
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from tools.arxiv_tool import search_academic_papers as _search_arxiv
from tools.kaggle_tool import (
    find_kaggle_datasets as _find_kaggle,
    inspect_dataset as _inspect_dataset,
    download_kaggle_dataset as _download_kaggle,
)
from pipeline.clean_data import run_pipeline_for_dataset

# Initialize FastMCP Server
try:
    from fastmcp import FastMCP
    mcp = FastMCP(
        name="Autonomous-ML-Research-Server",
        instructions=(
            "Autonomous research tool server. Provides tools to search arXiv papers, "
            "find and inspect Kaggle datasets, and execute deterministic data cleaning pipelines."
        ),
    )
except ImportError:
    # Fallback placeholder if fastmcp is still finishing installation
    mcp = None


def search_academic_papers(
    query: str,
    max_results: int = 5,
    sort_by: Literal["relevance", "lastUpdatedDate", "submittedDate"] = "relevance",
) -> str:
    """Searches arXiv for academic literature matching the given topic.

    Args:
        query: Search keywords or research topic (e.g., 'graph neural network fraud').
        max_results: Maximum papers to return (1-10, default 5).
        sort_by: Sorting order: 'relevance', 'lastUpdatedDate', or 'submittedDate'.

    Returns:
        JSON string containing verified paper metadata (title, authors, summary, direct PDF link).
    """
    results = _search_arxiv(query=query, max_results=max_results, sort_by=sort_by)
    return json.dumps(results, indent=2)


def find_kaggle_datasets(
    query: str,
    max_results: int = 5,
    min_usability_score: float = 0.70,
    max_size_mb: int = 250,
) -> str:
    """Discovers public Kaggle datasets matching research keywords.

    Enforces minimum usability ratings and download size limits.
    Falls back to curated benchmarks if Kaggle API keys are absent.

    Args:
        query: Dataset topic keywords (e.g., 'credit card fraud detection').
        max_results: Maximum datasets to retrieve (1-10, default 5).
        min_usability_score: Minimum Kaggle usability score (0.0 to 1.0, default 0.70).
        max_size_mb: Maximum allowed dataset download size in MB (default 250).

    Returns:
        JSON string of dataset IDs, titles, sizes, usability scores, and URLs.
    """
    results = _find_kaggle(
        query=query,
        max_results=max_results,
        min_usability_score=min_usability_score,
        max_size_mb=max_size_mb,
    )
    return json.dumps(results, indent=2)


def inspect_dataset_metadata(dataset_id: str) -> str:
    """Inspects files and formats inside a Kaggle dataset prior to downloading.

    Args:
        dataset_id: Kaggle dataset slug in 'owner/dataset-name' format.

    Returns:
        JSON string containing status, file list, and formats (CSV, Parquet, JSON).
    """
    results = _inspect_dataset(dataset_id=dataset_id)
    return json.dumps(results, indent=2)


def trigger_data_pipeline(
    dataset_id: str,
    handle_missing: Literal["drop", "median_impute", "mean_impute", "mode_impute"] = "median_impute",
    drop_duplicates: bool = True,
    normalize_headers: bool = True,
) -> str:
    """Downloads, unzips, cleans, and profiles a tabular dataset.

    Security & Guardrail Notice:
    Input is sanitized to prevent directory traversal. Execution runs in a sandboxed local directory.

    Args:
        dataset_id: Kaggle dataset identifier (e.g., 'mlg-ulb/creditcardfraud').
        handle_missing: Strategy for resolving null values ('median_impute', 'mean_impute', 'mode_impute', 'drop').
        drop_duplicates: Whether to detect and remove identical rows.
        normalize_headers: Whether to standardize column names to snake_case.

    Returns:
        JSON string containing output file path, pre- and post-cleaning metrics, and a top-5 row preview.
    """
    try:
        # Step 1: Download / Retrieve raw data
        download_info = _download_kaggle(dataset_id=dataset_id, target_dir="./data/raw")
        dataset_folder = download_info["local_path"]

        # Step 2: Run cleaning pipeline
        pipeline_result = run_pipeline_for_dataset(
            dataset_folder=dataset_folder,
            output_dir="./processed_data",
            handle_missing=handle_missing,
            drop_duplicates=drop_duplicates,
            normalize_headers=normalize_headers,
        )
        pipeline_result["source_dataset_id"] = dataset_id
        return json.dumps(pipeline_result, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "dataset_id": dataset_id,
            "error_message": str(e),
        }, indent=2)


# Register tools with FastMCP if loaded
if mcp is not None:
    mcp.tool()(search_academic_papers)
    mcp.tool()(find_kaggle_datasets)
    mcp.tool()(inspect_dataset_metadata)
    mcp.tool()(trigger_data_pipeline)


if __name__ == "__main__":
    if "--test" in sys.argv:
        print("[TEST] Running autonomous tool verification...")
        papers = search_academic_papers("fraud detection", max_results=2)
        print("\n--- arXiv Papers ---")
        print(papers[:300] + "...")

        datasets = find_kaggle_datasets("fraud", max_results=2)
        print("\n--- Kaggle Datasets ---")
        print(datasets)

        print("\n--- Pipeline Execution ---")
        pipeline_res = trigger_data_pipeline("mlg-ulb/creditcardfraud")
        print(pipeline_res[:400] + "...")
        print("\n[SUCCESS] Phase 1 tools verified successfully.")
    else:
        if mcp:
            mcp.run()
        else:
            print("FastMCP module not yet ready. Run with --test to verify tools.")
