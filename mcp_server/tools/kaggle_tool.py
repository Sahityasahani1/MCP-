"""Kaggle Dataset Discovery and Download Tool.

Handles authenticated search and download via the Kaggle API/CLI.
Provides SQLite TTL caching and an automated Benchmark/Mock mode if Kaggle credentials
are not yet configured, ensuring zero pipeline blockage during initial setup.
"""

import os
import re
import json
import zipfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from .cache import global_cache

DATASET_ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+$")

# Curated benchmark datasets for mock/demo mode when credentials are not configured
BENCHMARK_CATALOG = [
    {
        "dataset_id": "mlg-ulb/creditcardfraud",
        "title": "Credit Card Fraud Detection",
        "size_mb": 66.0,
        "usability_score": 0.85,
        "url": "https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud",
        "download_count": 520000,
        "tags": ["fraud", "finance", "classification", "imbalanced"],
    },
    {
        "dataset_id": "blastchar/telco-customer-churn",
        "title": "Telco Customer Churn",
        "size_mb": 0.95,
        "usability_score": 0.88,
        "url": "https://www.kaggle.com/datasets/blastchar/telco-customer-churn",
        "download_count": 310000,
        "tags": ["churn", "telecom", "classification", "tabular"],
    },
    {
        "dataset_id": "crawford/emnist",
        "title": "EMNIST Handwritten Characters",
        "size_mb": 210.0,
        "usability_score": 0.82,
        "url": "https://www.kaggle.com/datasets/crawford/emnist",
        "download_count": 180000,
        "tags": ["vision", "ocr", "deep learning", "handwritten"],
    },
    {
        "dataset_id": "camnugent/california-housing-prices",
        "title": "California Housing Prices",
        "size_mb": 1.4,
        "usability_score": 0.94,
        "url": "https://www.kaggle.com/datasets/camnugent/california-housing-prices",
        "download_count": 290000,
        "tags": ["housing", "regression", "geospatial", "tabular"],
    },
    {
        "dataset_id": "robikscube/hourly-energy-consumption",
        "title": "Hourly Energy Consumption (PJM)",
        "size_mb": 11.5,
        "usability_score": 0.88,
        "url": "https://www.kaggle.com/datasets/robikscube/hourly-energy-consumption",
        "download_count": 140000,
        "tags": ["time series", "energy", "forecasting", "tabular"],
    },
]


def _has_kaggle_credentials() -> bool:
    """Check if Kaggle authentication is available."""
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    if kaggle_json.exists():
        return True
    if os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY"):
        return True
    return False


def find_kaggle_datasets(
    query: str,
    max_results: int = 5,
    min_usability_score: float = 0.70,
    max_size_mb: int = 250,
    use_cache: bool = True,
) -> List[Dict[str, Any]]:
    """Search for Kaggle datasets matching user query with TTL caching."""
    clean_query = query.strip().lower()
    max_results = max(1, min(max_results, 10))
    cache_params = {
        "query": clean_query,
        "max_results": max_results,
        "min_usability_score": min_usability_score,
        "max_size_mb": max_size_mb,
    }

    # 1. Check TTL Cache
    if use_cache:
        cached = global_cache.get("kaggle_search", cache_params)
        if cached is not None:
            return cached

    # 2. Fetch or Benchmark Fallback
    if not _has_kaggle_credentials():
        q_tokens = [w for w in re.findall(r"\w+", clean_query) if len(w) > 2]
        matches = []
        for item in BENCHMARK_CATALOG:
            item_text = (item["title"] + " " + item["dataset_id"] + " " + " ".join(item["tags"])).lower()
            matched_tokens = [t for t in q_tokens if t in item_text]
            if matched_tokens or not clean_query:
                if item["size_mb"] <= max_size_mb and item["usability_score"] >= min_usability_score:
                    matches.append({
                        **item,
                        "is_mock_demo": True,
                        "_relevance": len(matched_tokens) if matched_tokens else 0,
                    })

        matches.sort(key=lambda x: x.get("_relevance", 0), reverse=True)
        for m in matches:
            m.pop("_relevance", None)

        # Only return fallback benchmark items if query is empty or matched relevant tokens
        if not matches and not clean_query:
            matches = [{**item, "is_mock_demo": True} for item in BENCHMARK_CATALOG[:max_results]]
        results = matches[:max_results]
    else:
        try:
            from kaggle.api.kaggle_api_extended import KaggleApi
            api = KaggleApi()
            api.authenticate()

            raw_datasets = api.dataset_list(search=clean_query, sort_by="votes", max_size=max_size_mb * 1024 * 1024)
            results = []
            for ds in raw_datasets:
                dataset_id = getattr(ds, "ref", f"{getattr(ds, 'ownerName', '')}/{getattr(ds, 'name', '')}")
                size_mb = round(getattr(ds, "totalBytes", 0) / (1024 * 1024), 2)
                usability = getattr(ds, "usabilityRating", 0.75)

                if usability >= min_usability_score and size_mb <= max_size_mb:
                    results.append({
                        "dataset_id": dataset_id,
                        "title": getattr(ds, "title", dataset_id),
                        "size_mb": size_mb,
                        "usability_score": usability,
                        "url": f"https://www.kaggle.com/datasets/{dataset_id}",
                        "download_count": getattr(ds, "downloadCount", 0),
                        "is_mock_demo": False,
                    })
                if len(results) >= max_results:
                    break
        except Exception as e:
            q_tokens = [w for w in re.findall(r"\w+", clean_query) if len(w) > 2]
            matched_fb = [
                {**item, "is_mock_demo": True, "note": f"Fallback: {str(e)[:60]}"}
                for item in BENCHMARK_CATALOG
                if any(t in (item["title"] + " " + " ".join(item["tags"])).lower() for t in q_tokens) or not clean_query
            ]
            results = matched_fb[:max_results]

    # 3. Cache result
    if use_cache and results:
        global_cache.set("kaggle_search", cache_params, results, ttl_seconds=86400)

    return results


def inspect_dataset(dataset_id: str) -> Dict[str, Any]:
    """Inspect dataset metadata and file structure prior to download."""
    if not DATASET_ID_REGEX.match(dataset_id):
        raise ValueError(f"Invalid dataset_id format: '{dataset_id}'. Must match 'owner/dataset-name'.")

    if not _has_kaggle_credentials():
        return {
            "dataset_id": dataset_id,
            "status": "available",
            "files": ["data.csv", "metadata.json"],
            "formats": ["CSV"],
            "estimated_rows": 10000,
            "demo_mode": True,
        }

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()

        files_obj = api.dataset_list_files(dataset_id)
        filenames = [f.name for f in getattr(files_obj, "files", [])]

        return {
            "dataset_id": dataset_id,
            "status": "available",
            "files": filenames[:10],
            "formats": list({f.split(".")[-1].upper() for f in filenames if "." in f}),
            "total_files": len(filenames),
            "demo_mode": False,
        }
    except Exception as e:
        return {
            "dataset_id": dataset_id,
            "status": "error",
            "error_message": str(e),
            "demo_mode": True,
        }


def download_kaggle_dataset(
    dataset_id: str,
    target_dir: str = "./data/raw",
) -> Dict[str, Any]:
    """Download and extract a Kaggle dataset into a localized raw storage directory."""
    if not DATASET_ID_REGEX.match(dataset_id):
        raise ValueError(f"Invalid dataset_id format: '{dataset_id}'. Must match 'owner/dataset-name'.")

    sanitized_folder = dataset_id.replace("/", "_")
    output_path = Path(target_dir).resolve() / sanitized_folder
    output_path.mkdir(parents=True, exist_ok=True)

    if not _has_kaggle_credentials():
        sample_csv = output_path / "dataset.csv"
        if not sample_csv.exists():
            import pandas as pd
            import numpy as np

            np.random.seed(42)
            n_rows = 500
            df = pd.DataFrame({
                "User ID": [f"USR_{i:04d}" for i in range(n_rows)],
                " Transaction Amount ($) ": np.random.uniform(5.0, 1500.0, size=n_rows).round(2),
                "Customer_Age": np.random.choice([19, 25, 34, 45, 62, np.nan], size=n_rows, p=[0.2, 0.3, 0.2, 0.15, 0.1, 0.05]),
                "Risk_Score": np.random.normal(0.5, 0.15, size=n_rows),
                "Is_Fraudulent": np.random.choice([0, 1], size=n_rows, p=[0.94, 0.06]),
            })
            df = pd.concat([df, df.iloc[:15]], ignore_index=True)
            df.to_csv(sample_csv, index=False)

        return {
            "status": "downloaded",
            "dataset_id": dataset_id,
            "local_path": str(output_path),
            "files": [f.name for f in output_path.glob("*.csv")],
            "is_mock_generated": True,
            "message": "Generated structured benchmark CSV (Kaggle credentials not supplied).",
        }

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()

        api.dataset_download_files(dataset_id, path=str(output_path), unzip=True, quiet=False)
        csv_files = [f.name for f in output_path.glob("*.csv")]
        return {
            "status": "downloaded",
            "dataset_id": dataset_id,
            "local_path": str(output_path),
            "files": [f.name for f in output_path.iterdir()],
            "csv_files": csv_files,
            "is_mock_generated": False,
        }
    except Exception as e:
        raise RuntimeError(f"Kaggle download failed: {str(e)}")
