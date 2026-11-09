"""Hugging Face Datasets Hub Discovery Tool.

Searches 150,000+ open-source machine learning datasets on Hugging Face Hub (huggingface.co)
via the public REST API. Provides rich metadata (downloads, likes, formats, direct repository URLs)
and sub-millisecond SQLite TTL caching.
"""

from typing import List, Dict, Any, Optional
import urllib.parse
import urllib.request
import json
from .cache import global_cache

# Curated fallback benchmark datasets from Hugging Face Hub
HF_BENCHMARK_CATALOG = [
    {
        "dataset_id": "vitaliy-sharandin/synthetic-fraud-detection",
        "title": "Synthetic Fraud Detection (Tabular)",
        "size_mb": 42.0,
        "usability_score": 0.89,
        "url": "https://huggingface.co/datasets/vitaliy-sharandin/synthetic-fraud-detection",
        "download_count": 8500,
        "likes": 45,
        "tags": ["fraud", "synthetic", "finance", "tabular"],
        "source": "Hugging Face",
        "is_mock_demo": True,
    },
    {
        "dataset_id": "scikit-learn/adult-census-income",
        "title": "Adult Census Income Benchmark",
        "size_mb": 3.8,
        "usability_score": 0.95,
        "url": "https://huggingface.co/datasets/scikit-learn/adult-census-income",
        "download_count": 92000,
        "likes": 120,
        "tags": ["classification", "census", "tabular", "benchmark"],
        "source": "Hugging Face",
        "is_mock_demo": True,
    },
    {
        "dataset_id": "mstz/heart-failure",
        "title": "Heart Failure Clinical Records",
        "size_mb": 0.5,
        "usability_score": 0.92,
        "url": "https://huggingface.co/datasets/mstz/heart-failure",
        "download_count": 18500,
        "likes": 38,
        "tags": ["healthcare", "tabular", "clinical", "classification"],
        "source": "Hugging Face",
        "is_mock_demo": True,
    },
]


def _format_title(dataset_id: str) -> str:
    """Converts a repository slug like 'vitaliy-sharandin/synthetic-fraud-detection' into 'Synthetic Fraud Detection'."""
    name_part = dataset_id.split("/")[-1] if "/" in dataset_id else dataset_id
    cleaned = name_part.replace("-", " ").replace("_", " ")
    return cleaned.title()


def _estimate_size_mb(tags: List[str]) -> float:
    """Estimates dataset size in MB from Hugging Face size_categories tag."""
    for tag in tags:
        if tag.startswith("size_categories:"):
            cat = tag.split(":")[-1]
            if "n<1K" in cat:
                return 0.2
            elif "1K<n<10K" in cat:
                return 1.5
            elif "10K<n<100K" in cat:
                return 12.0
            elif "100K<n<1M" in cat:
                return 48.0
            elif "1M<n<10M" in cat:
                return 120.0
            elif "10M<n<100M" in cat:
                return 220.0
    return 15.0


def _compute_usability_score(downloads: int, likes: int) -> float:
    """Calculates normalized usability score (0.70 to 0.98) based on community adoption."""
    raw = 0.75 + min(0.15, (downloads / 5000.0) * 0.1) + min(0.08, (likes / 100.0) * 0.08)
    return round(min(0.98, max(0.70, raw)), 2)


def find_huggingface_datasets(
    query: str,
    max_results: int = 5,
    use_cache: bool = True,
) -> List[Dict[str, Any]]:
    """Discovers public machine learning datasets from Hugging Face Hub with TTL caching.

    Args:
        query: Research or dataset topic keywords.
        max_results: Maximum datasets to retrieve (1-10, default 5).
        use_cache: Whether to use SQLite TTL cache.

    Returns:
        List of dataset metadata dictionaries including ID, title, size, usability, downloads, and URLs.
    """
    clean_query = query.strip()
    if not clean_query:
        return []

    max_results = max(1, min(max_results, 10))
    cache_params = {"query": clean_query, "max_results": max_results}

    # 1. Check TTL Cache
    if use_cache:
        cached = global_cache.get("hf_dataset_search", cache_params)
        if cached is not None:
            return cached

    # 2. Fetch from Hugging Face REST API
    params = {
        "search": clean_query,
        "limit": max_results,
        "full": "true",
    }
    url = f"https://huggingface.co/api/datasets?{urllib.parse.urlencode(params)}"
    headers = {
        "User-Agent": "AMRA-Research-Agent/3.0",
        "Accept": "application/json",
    }

    results: List[Dict[str, Any]] = []

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as response:
            items = json.loads(response.read().decode("utf-8"))
            for item in items:
                dataset_id = item.get("id", "")
                if not dataset_id:
                    continue

                downloads = int(item.get("downloads", 0) or 0)
                likes = int(item.get("likes", 0) or 0)
                tags = [str(t) for t in (item.get("tags") or [])]
                size_mb = _estimate_size_mb(tags)
                usability = _compute_usability_score(downloads, likes)

                results.append({
                    "dataset_id": dataset_id,
                    "title": _format_title(dataset_id),
                    "size_mb": size_mb,
                    "usability_score": usability,
                    "url": f"https://huggingface.co/datasets/{dataset_id}",
                    "download_count": downloads,
                    "likes": likes,
                    "tags": tags[:6],
                    "source": "Hugging Face",
                    "is_mock_demo": False,
                })
    except Exception:
        # Fallback to relevant items from HF_BENCHMARK_CATALOG
        q_tokens = clean_query.lower().split()
        matched = [
            cat for cat in HF_BENCHMARK_CATALOG
            if any(t in cat["dataset_id"].lower() or any(t in tag for tag in cat["tags"]) for t in q_tokens)
        ]
        results = (matched or HF_BENCHMARK_CATALOG)[:max_results]

    # If no results returned from API, fallback to catalog
    if not results:
        results = HF_BENCHMARK_CATALOG[:max_results]

    # 3. Store in TTL Cache
    if use_cache and results:
        global_cache.set("hf_dataset_search", cache_params, results, ttl_seconds=86400)

    return results
