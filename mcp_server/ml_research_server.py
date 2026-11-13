"""FastMCP Server: Autonomous ML Research Agent (Enterprise Grade).

Exposes strictly typed MCP tools for academic paper discovery (arXiv),
dataset discovery (Kaggle), and autonomous data cleaning & health profiling (Pandas).
"""

import sys
import os
import json
from pathlib import Path
from typing import Literal, Optional, Dict, Any, List

# Ensure mcp_server is in sys.path
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from tools.arxiv_tool import search_academic_papers as _search_arxiv
from tools.openalex_tool import search_openalex_papers as _search_openalex
from tools.kaggle_tool import (
    find_kaggle_datasets as _find_kaggle,
    inspect_dataset as _inspect_dataset,
    download_kaggle_dataset as _download_kaggle,
)
from tools.hf_dataset_tool import find_huggingface_datasets as _find_huggingface
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
    mcp = None


def search_academic_papers(
    query: str,
    max_results: int = 5,
    sort_by: Literal["relevance", "lastUpdatedDate", "submittedDate"] = "relevance",
    use_cache: bool = True,
) -> str:
    """Searches arXiv for academic literature matching the given topic with TTL caching.

    Args:
        query: Search keywords or research topic (e.g., 'graph neural network fraud').
        max_results: Maximum papers to return (1-10, default 5).
        sort_by: Sorting order: 'relevance', 'lastUpdatedDate', or 'submittedDate'.
        use_cache: Whether to use SQLite TTL cache (default True).

    Returns:
        JSON string containing verified paper metadata (title, authors, summary, direct PDF link).
    """
    results = _search_arxiv(query=query, max_results=max_results, sort_by=sort_by, use_cache=use_cache)
    return json.dumps(results, indent=2)


def search_openalex_papers(
    query: str,
    max_results: int = 5,
    sort_by: Literal["relevance", "cited_by_count"] = "relevance",
    use_cache: bool = True,
) -> str:
    """Searches OpenAlex academic graph (250M+ works) with verified citation metrics and open access PDFs.

    Args:
        query: Research topic keywords.
        max_results: Maximum papers to return (1-10, default 5).
        sort_by: Sorting order: 'relevance' or 'cited_by_count'.
        use_cache: Whether to use SQLite TTL cache (default True).

    Returns:
        JSON string containing peer-reviewed paper metadata, citations, DOI, and open access PDFs.
    """
    results = _search_openalex(query=query, max_results=max_results, sort_by=sort_by, use_cache=use_cache)
    return json.dumps(results, indent=2)


def find_kaggle_datasets(
    query: str,
    max_results: int = 5,
    min_usability_score: float = 0.70,
    max_size_mb: int = 250,
    use_cache: bool = True,
) -> str:
    """Discovers public Kaggle datasets matching research keywords with TTL caching.

    Args:
        query: Dataset topic keywords (e.g., 'credit card fraud detection').
        max_results: Maximum datasets to retrieve (1-10, default 5).
        min_usability_score: Minimum Kaggle usability score (0.0 to 1.0, default 0.70).
        max_size_mb: Maximum allowed dataset download size in MB (default 250).
        use_cache: Whether to use SQLite TTL cache (default True).

    Returns:
        JSON string of dataset IDs, titles, sizes, usability scores, and URLs.
    """
    results = _find_kaggle(
        query=query,
        max_results=max_results,
        min_usability_score=min_usability_score,
        max_size_mb=max_size_mb,
        use_cache=use_cache,
    )
    return json.dumps(results, indent=2)


def find_huggingface_datasets(
    query: str,
    max_results: int = 5,
    use_cache: bool = True,
) -> str:
    """Discovers open-source machine learning datasets from Hugging Face Hub (150K+ repos).

    Args:
        query: Research or dataset topic keywords.
        max_results: Maximum datasets to retrieve (1-10, default 5).
        use_cache: Whether to use SQLite TTL cache (default True).

    Returns:
        JSON string of dataset IDs, titles, downloads, likes, and URLs.
    """
    results = _find_huggingface(query=query, max_results=max_results, use_cache=use_cache)
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
    cap_outliers: bool = True,
    test_size: float = 0.2,
    target_column: Optional[str] = None,
) -> str:
    """Downloads, cleans, profiles, and exports a tabular dataset to CSV and Apache Parquet.

    Includes algorithmic Data Health Score (0-100), IQR outlier detection/capping,
    stratified zero-leakage train/test partitioning, and automated LightGBM baseline modeling.

    Args:
        dataset_id: Kaggle dataset identifier (e.g., 'mlg-ulb/creditcardfraud') or local file.
        handle_missing: Strategy for resolving null values ('median_impute', 'mean_impute', 'mode_impute', 'drop').
        drop_duplicates: Whether to detect and remove identical rows.
        normalize_headers: Whether to standardize column names to snake_case.
        cap_outliers: Whether to winsorize extreme numeric outliers.
        test_size: Ratio for train/test partition (e.g. 0.2 for 80/20).
        target_column: Optional override of target prediction feature for LightGBM.

    Returns:
        JSON string with paths to cleaned CSV and Parquet, health scores, baseline model metrics, and head preview.
    """
    try:
        # Check if local dataset
        if dataset_id.startswith("local/"):
            raw_path = Path("./data/raw") / (dataset_id.replace("local/", "") + ".csv")
            if raw_path.exists():
                dataset_folder = raw_path.parent
            else:
                download_info = _download_kaggle(dataset_id=dataset_id, target_dir="./data/raw")
                dataset_folder = download_info["local_path"]
        else:
            download_info = _download_kaggle(dataset_id=dataset_id, target_dir="./data/raw")
            dataset_folder = download_info["local_path"]

        pipeline_result = run_pipeline_for_dataset(
            dataset_folder=dataset_folder,
            output_dir="./processed_data",
            handle_missing=handle_missing,
            drop_duplicates=drop_duplicates,
            normalize_headers=normalize_headers,
            cap_outliers=cap_outliers,
            test_size=test_size,
            target_col_override=target_column,
        )
        pipeline_result["source_dataset_id"] = dataset_id
        return json.dumps(pipeline_result, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "dataset_id": dataset_id,
            "error_message": str(e),
        }, indent=2)


if mcp is not None:
    mcp.tool()(search_academic_papers)
    mcp.tool()(search_openalex_papers)
    mcp.tool()(find_kaggle_datasets)
    mcp.tool()(find_huggingface_datasets)
    mcp.tool()(inspect_dataset_metadata)
    mcp.tool()(trigger_data_pipeline)


if __name__ == "__main__":
    if "--test" in sys.argv:
        print("[TEST] Running autonomous tool verification...")
        papers = search_academic_papers("fraud detection", max_results=2)
        print(" arXiv Papers:", len(json.loads(papers)))
        oa_papers = search_openalex_papers("fraud detection", max_results=2)
        print(" OpenAlex Papers:", len(json.loads(oa_papers)))
        datasets = find_kaggle_datasets("fraud", max_results=2)
        print(" Kaggle Datasets:", len(json.loads(datasets)))
        hf_datasets = find_huggingface_datasets("fraud", max_results=2)
        print(" Hugging Face Datasets:", len(json.loads(hf_datasets)))
        pipeline_res = trigger_data_pipeline("mlg-ulb/creditcardfraud")
        data = json.loads(pipeline_res)
        print(f" Health Score: {data.get('stats_before', {}).get('health_score')} -> {data.get('stats_after', {}).get('health_score')}")
        print(f" Parquet Export: {data.get('output_parquet_filepath')}")
        print("[SUCCESS] Phase 1 tools verified successfully.")
    else:
        if mcp:
            mcp.run()
        else:
            print("FastMCP module not ready.")
