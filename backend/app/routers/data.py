"""Data Management & File Download Router (Hardened Security)."""

import io
import re
import secrets
import pandas as pd
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Response
from fastapi.responses import FileResponse
from pathlib import Path
from ..config import settings
from ..auth import verify_api_key
from ..cache import app_cache, apply_edge_cache_headers

router = APIRouter(prefix="/api/data", tags=["Data Artifacts"], dependencies=[Depends(verify_api_key)])

# Strict security regex: alphanumerics, dashes, underscores, and single dot for extension
SAFE_FILENAME_REGEX = re.compile(r"^[a-zA-Z0-9_\-]+\.(csv|parquet)$")


@router.get("/processed")
async def list_processed_files(response: Response):
    """Returns a list of all cleaned CSV and Parquet files ready for ML modeling with caching."""
    cache_key = "data:processed_file_list"
    cached, hit, age = app_cache.get(cache_key)
    if hit and cached:
        apply_edge_cache_headers(response, ttl_seconds=15, is_hit=True, age_seconds=age)
        return cached

    processed_dir = settings.DATA_PROCESSED_DIR.resolve()
    if not processed_dir.exists():
        payload = {"files": []}
        app_cache.set(cache_key, payload, ttl=15)
        apply_edge_cache_headers(response, ttl_seconds=15, is_hit=False)
        return payload

    files = []
    for f in processed_dir.iterdir():
        if f.suffix in [".csv", ".parquet"]:
            files.append({
                "filename": f.name,
                "format": f.suffix[1:].upper(),
                "size_bytes": f.stat().st_size,
                "modified_at": f.stat().st_mtime,
            })
    payload = {"files": files}
    app_cache.set(cache_key, payload, ttl=15)
    apply_edge_cache_headers(response, ttl_seconds=15, is_hit=False)
    return payload


@router.get("/download/{filename}")
async def download_file(filename: str):
    """Safely downloads a cleaned dataset file with strict path traversal & extension protection."""
    # 1. Regex validation against path traversal characters, directory separators, and disallowed extensions
    if not SAFE_FILENAME_REGEX.match(filename) or ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename format or disallowed extension.")

    # 2. Strict path resolution check
    file_path = (settings.DATA_PROCESSED_DIR / filename).resolve()
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    # 3. Assert file is strictly inside DATA_PROCESSED_DIR (Defense in Depth)
    if settings.DATA_PROCESSED_DIR.resolve() not in file_path.parents:
        raise HTTPException(status_code=403, detail="Access denied: outside directory boundary.")

    media_type = "text/csv" if filename.endswith(".csv") else "application/octet-stream"
    return FileResponse(path=file_path, filename=filename, media_type=media_type)


@router.post("/upload")
async def upload_csv_dataset(file: UploadFile = File(...)):
    """Safely uploads a custom tabular CSV dataset into data/raw/ using chunked streaming with DoS boundaries."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files (.csv) are accepted.")

    # Sanitize filename
    clean_stem = re.sub(r"[^a-zA-Z0-9_\-]", "_", file.filename[:-4])[:50]
    clean_name = f"{clean_stem}.csv"
    if not SAFE_FILENAME_REGEX.match(clean_name):
        raise HTTPException(status_code=400, detail="Invalid filename characters.")

    raw_dir = settings.DATA_RAW_DIR.resolve()
    raw_dir.mkdir(parents=True, exist_ok=True)
    target_path = (raw_dir / clean_name).resolve()

    if raw_dir not in target_path.parents and raw_dir != target_path.parent:
        raise HTTPException(status_code=403, detail="Directory traversal attempt detected.")

    # Prevent silent overwrite collisions by appending a short cryptographic token if file already exists
    if target_path.exists():
        clean_stem = f"{clean_stem}_{secrets.token_hex(3)}"
        clean_name = f"{clean_stem}.csv"
        target_path = (raw_dir / clean_name).resolve()

    # Stream chunks directly to disk with hard 250MB RAM protection
    max_bytes = 250 * 1024 * 1024
    chunk_size = 1024 * 1024  # 1 MB chunk buffer
    total_bytes = 0

    try:
        with open(target_path, "wb") as f:
            while chunk := await file.read(chunk_size):
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    f.close()
                    target_path.unlink(missing_ok=True)
                    raise HTTPException(status_code=400, detail="File exceeds 250 MB ceiling limit.")
                f.write(chunk)
    except HTTPException:
        raise
    except Exception as exc:
        target_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to write file: {str(exc)}")

    # Inspect preview safely from written file
    try:
        df = pd.read_csv(target_path, nrows=10)
        num_cols = len(df.columns)
        headers = list(df.columns[:10])
        preview_rows = df.head(5).to_dict(orient="records")
    except Exception as exc:
        target_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(exc)}")

    return {
        "status": "success",
        "filename": clean_name,
        "dataset_id": f"local/{clean_stem}",
        "size_bytes": total_bytes,
        "columns_count": num_cols,
        "sample_headers": headers,
        "preview": preview_rows,
        "message": f"Dataset {clean_name} uploaded successfully and ready for autonomous cleaning.",
    }
