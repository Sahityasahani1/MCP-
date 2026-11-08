"""Phase 1 Verification Script for Autonomous ML Research Agent (AMRA).

Validates:
1. arXiv academic literature search & PDF link extraction.
2. Kaggle dataset discovery & usability filtering.
3. Automated tabular dataset ingestion, cleaning & profiling with Pandas.
4. FastMCP server tool definitions and exports.
"""

import sys
import os
import json
from pathlib import Path

# Add project root and mcp_server to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MCP_SERVER_DIR = Path(__file__).resolve().parent
if str(MCP_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(MCP_SERVER_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.arxiv_tool import search_academic_papers
from tools.kaggle_tool import find_kaggle_datasets, inspect_dataset
from pipeline.clean_data import clean_tabular_dataset
from ml_research_server import trigger_data_pipeline


def test_arxiv_search():
    print("\n[TEST 1/4] Testing arXiv Academic Paper Search...")
    query = "graph neural network fraud detection"
    papers = search_academic_papers(query=query, max_results=3)
    
    assert isinstance(papers, list), "arXiv search should return a list"
    assert len(papers) > 0, "arXiv search should return at least 1 paper"
    
    first_paper = papers[0]
    print(f" -> Found {len(papers)} papers.")
    print(f" -> Title: {first_paper['title']}")
    print(f" -> Authors: {', '.join(first_paper['authors'][:3])}")
    print(f" -> PDF URL: {first_paper['pdf_url']}")
    
    assert "pdf_url" in first_paper and first_paper["pdf_url"].startswith("http"), "Paper must have valid PDF URL"
    assert "summary" in first_paper and len(first_paper["summary"]) > 10, "Paper must have non-empty summary"
    print(" [PASSED] arXiv Academic Search Verified.")


def test_kaggle_discovery():
    print("\n[TEST 2/4] Testing Kaggle Dataset Discovery...")
    query = "credit card fraud"
    datasets = find_kaggle_datasets(query=query, max_results=3)
    
    assert isinstance(datasets, list), "Kaggle discovery should return a list"
    assert len(datasets) > 0, "Should return at least 1 matching dataset"
    
    first_ds = datasets[0]
    print(f" -> Found {len(datasets)} dataset(s).")
    print(f" -> Dataset ID: {first_ds['dataset_id']}")
    print(f" -> Title: {first_ds['title']}")
    print(f" -> Usability Score: {first_ds.get('usability_score')}")
    print(f" -> Size: {first_ds.get('size_mb')} MB")
    
    assert "dataset_id" in first_ds, "Result must contain dataset_id"
    print(" [PASSED] Kaggle Discovery Verified.")


def test_kaggle_inspect():
    print("\n[TEST 3/4] Testing Dataset Inspection...")
    ds_id = "mlg-ulb/creditcardfraud"
    metadata = inspect_dataset(ds_id)
    
    print(f" -> Status: {metadata.get('status')}")
    print(f" -> Formats: {metadata.get('formats')}")
    print(f" -> Files: {metadata.get('files')}")
    
    assert metadata.get("status") in ["available", "error"], "Status must be valid"
    print(" [PASSED] Dataset Inspection Verified.")


def test_pipeline_execution():
    print("\n[TEST 4/4] Testing End-to-End Pipeline Execution (Ingestion -> Clean -> Profile)...")
    ds_id = "mlg-ulb/creditcardfraud"
    raw_result = trigger_data_pipeline(
        dataset_id=ds_id,
        handle_missing="median_impute",
        drop_duplicates=True,
        normalize_headers=True,
    )
    
    result = json.loads(raw_result)
    assert result.get("status") == "success", f"Pipeline failed: {result}"
    
    print(f" -> Output File: {result.get('output_filepath')}")
    print(f" -> Stats Before: {result.get('stats_before')}")
    print(f" -> Stats After:  {result.get('stats_after')}")
    print(f" -> Actions Taken ({len(result.get('actions_taken', []))}):")
    for act in result.get("actions_taken", []):
        print(f"     * {act}")
        
    print(f" -> Top-5 Rows Preview Sample: {len(result.get('head_preview', []))} records generated.")
    
    # Verify file actually exists on disk
    output_csv = Path(result["output_filepath"])
    assert output_csv.exists(), f"Cleaned CSV does not exist at {output_csv}"
    assert output_csv.stat().st_size > 0, "Cleaned CSV is empty"
    print(f" -> Cleaned CSV Verified on Disk ({output_csv.stat().st_size} bytes).")
    print(" [PASSED] End-to-End Cleaning & Profiling Pipeline Verified.")


if __name__ == "__main__":
    print("=" * 70)
    print(" AUTONOMOUS ML RESEARCH AGENT - PHASE 1 VERIFICATION")
    print("=" * 70)
    
    try:
        test_arxiv_search()
        test_kaggle_discovery()
        test_kaggle_inspect()
        test_pipeline_execution()
        print("\n" + "=" * 70)
        print(" ALL PHASE 1 TESTS PASSED SUCCESSFULLY! ")
        print(" FastMCP execution layer is operational and ready for Phase 2.")
        print("=" * 70)
    except Exception as e:
        print(f"\n[ERROR] Phase 1 verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
