"""Autonomous Data Cleaning and Profiling Pipeline.

Provides deterministic tabular data manipulation:
- Header normalization (snake_case conversion, stripping symbols)
- Duplicate row detection and removal
- Missing value imputation (median, mean, mode) or dropping
- Comprehensive pre- and post-cleaning profiling metrics
- Top-5 preview output formatted as JSON for web UI rendering
"""

import argparse
import json
import os
import re
from pathlib import Path
from typing import Dict, Any, Literal, List, Optional
import numpy as np
import pandas as pd


def _to_snake_case(col_name: str) -> str:
    """Standardizes dirty column names to clean snake_case."""
    s = col_name.strip()
    s = re.sub(r"[^\w\s-]", "", s)  # Remove symbols like $, %, #
    s = re.sub(r"[\s-]+", "_", s)   # Replace spaces/dashes with underscore
    return s.lower()


def clean_tabular_dataset(
    input_path: str | Path,
    output_dir: str | Path = "./processed_data",
    handle_missing: Literal["drop", "median_impute", "mean_impute", "mode_impute"] = "median_impute",
    drop_duplicates: bool = True,
    normalize_headers: bool = True,
    dataset_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Cleans a tabular dataset and returns structured health metrics.

    Args:
        input_path: Absolute or relative path to the raw CSV file.
        output_dir: Directory where the cleaned CSV will be saved.
        handle_missing: Strategy for resolving NaN/Null values.
        drop_duplicates: Whether to drop duplicate rows.
        normalize_headers: Whether to standardize column names to snake_case.
        dataset_name: Optional custom prefix for the output filename.

    Returns:
        Structured dictionary with before/after stats, actions taken, and head preview.
    """
    input_file = Path(input_path).resolve()
    if not input_file.exists():
        raise FileNotFoundError(f"Input data file does not exist: {input_file}")

    output_folder = Path(output_dir).resolve()
    output_folder.mkdir(parents=True, exist_ok=True)

    # 1. Load Data
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        raise ValueError(f"Failed to parse CSV file: {str(e)}")

    actions_taken: List[str] = []

    # 2. Record Pre-Cleaning Stats
    stats_before = {
        "rows": int(len(df)),
        "cols": int(len(df.columns)),
        "null_count": int(df.isnull().sum().sum()),
        "duplicate_count": int(df.duplicated().sum()),
    }

    # 3. Header Normalization
    if normalize_headers:
        old_cols = list(df.columns)
        new_cols = [_to_snake_case(c) for c in old_cols]
        # Ensure unique column names if collision occurs
        seen = {}
        unique_cols = []
        for c in new_cols:
            if c not in seen:
                seen[c] = 0
                unique_cols.append(c)
            else:
                seen[c] += 1
                unique_cols.append(f"{c}_{seen[c]}")
        df.columns = unique_cols
        actions_taken.append(f"Normalized {len(df.columns)} columns to snake_case.")

    # 4. Duplicate Removal
    if drop_duplicates and stats_before["duplicate_count"] > 0:
        dups_removed = stats_before["duplicate_count"]
        df = df.drop_duplicates()
        actions_taken.append(f"Removed {dups_removed} duplicate row(s).")

    # 5. Missing Value Imputation
    null_cols = df.columns[df.isnull().any()].tolist()
    if null_cols:
        if handle_missing == "drop":
            rows_before = len(df)
            df = df.dropna()
            actions_taken.append(f"Dropped {rows_before - len(df)} row(s) containing missing values.")
        else:
            for col in null_cols:
                col_nulls = int(df[col].isnull().sum())
                if pd.api.types.is_numeric_dtype(df[col]):
                    if handle_missing == "median_impute":
                        val = df[col].median()
                        df[col] = df[col].fillna(val)
                        actions_taken.append(f"Imputed {col_nulls} nulls in numeric '{col}' with median ({round(val, 2)}).")
                    elif handle_missing == "mean_impute":
                        val = df[col].mean()
                        df[col] = df[col].fillna(val)
                        actions_taken.append(f"Imputed {col_nulls} nulls in numeric '{col}' with mean ({round(val, 2)}).")
                    elif handle_missing == "mode_impute":
                        mode_val = df[col].mode()
                        val = mode_val[0] if len(mode_val) > 0 else 0
                        df[col] = df[col].fillna(val)
                        actions_taken.append(f"Imputed {col_nulls} nulls in '{col}' with mode ({val}).")
                else:
                    # Non-numeric: impute with mode or 'unknown'
                    mode_val = df[col].mode()
                    val = str(mode_val[0]) if len(mode_val) > 0 else "unknown"
                    df[col] = df[col].fillna(val)
                    actions_taken.append(f"Imputed {col_nulls} categorical nulls in '{col}' with mode ('{val}').")

    # 6. Post-Cleaning Stats
    stats_after = {
        "rows": int(len(df)),
        "cols": int(len(df.columns)),
        "null_count": int(df.isnull().sum().sum()),
        "duplicate_count": int(df.duplicated().sum()),
    }

    # 7. Save Cleaned Dataset
    prefix = dataset_name or input_file.stem
    output_filename = f"{prefix}_cleaned.csv"
    output_path = output_folder / output_filename
    df.to_csv(output_path, index=False)

    # 8. Generate Head Preview (clean JSON serializable)
    preview_df = df.head(5).copy()
    # Replace any remaining NaNs with None for valid JSON serialization
    preview_records = json.loads(preview_df.to_json(orient="records"))

    dtypes_dict = {col: str(dtype) for col, dtype in df.dtypes.items()}

    return {
        "status": "success",
        "dataset_name": prefix,
        "input_filepath": str(input_file),
        "output_filepath": str(output_path),
        "output_filename": output_filename,
        "stats_before": stats_before,
        "stats_after": stats_after,
        "actions_taken": actions_taken,
        "columns": list(df.columns),
        "dtypes": dtypes_dict,
        "head_preview": preview_records,
    }


def run_pipeline_for_dataset(
    dataset_folder: str | Path,
    output_dir: str | Path = "./processed_data",
    handle_missing: str = "median_impute",
    drop_duplicates: bool = True,
    normalize_headers: bool = True,
) -> Dict[str, Any]:
    """Finds first CSV in downloaded dataset folder and runs cleaning pipeline."""
    folder = Path(dataset_folder).resolve()
    csv_candidates = list(folder.glob("*.csv"))
    if not csv_candidates:
        # Search subdirectories
        csv_candidates = list(folder.rglob("*.csv"))

    if not csv_candidates:
        raise FileNotFoundError(f"No CSV file found inside dataset directory: {folder}")

    # Pick largest CSV if multiple exist
    primary_csv = max(csv_candidates, key=lambda f: f.stat().st_size)
    dataset_name = folder.name

    return clean_tabular_dataset(
        input_path=primary_csv,
        output_dir=output_dir,
        handle_missing=handle_missing,  # type: ignore
        drop_duplicates=drop_duplicates,
        normalize_headers=normalize_headers,
        dataset_name=dataset_name,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean tabular dataset and report profiling stats.")
    parser.add_argument("--input", required=True, help="Path to input CSV file")
    parser.add_argument("--output-dir", default="./processed_data", help="Output directory for cleaned CSV")
    parser.add_argument("--missing", choices=["drop", "median_impute", "mean_impute", "mode_impute"], default="median_impute")
    parser.add_argument("--no-duplicates-drop", action="store_true", help="Keep duplicate rows")
    parser.add_argument("--no-header-norm", action="store_true", help="Skip snake_case header normalization")
    parser.add_argument("--name", default=None, help="Output dataset identifier")

    args = parser.parse_args()
    result = clean_tabular_dataset(
        input_path=args.input,
        output_dir=args.output_dir,
        handle_missing=args.missing,
        drop_duplicates=not args.no_duplicates_drop,
        normalize_headers=not args.no_header_norm,
        dataset_name=args.name,
    )
    print(json.dumps(result, indent=2))
