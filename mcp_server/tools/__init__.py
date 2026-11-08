"""MCP Tools package for academic paper and dataset discovery."""
from .arxiv_tool import search_academic_papers
from .kaggle_tool import find_kaggle_datasets, inspect_dataset, download_kaggle_dataset

__all__ = [
    "search_academic_papers",
    "find_kaggle_datasets",
    "inspect_dataset",
    "download_kaggle_dataset",
]
