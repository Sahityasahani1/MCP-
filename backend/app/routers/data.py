"""Data Management & File Download Router (Hardened Security)."""

import re
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from ..config import settings

router = APIRouter(prefix="/api/data", tags=["Data Artifacts"])

# Strict security regex: alphanumerics, dashes, underscores, and single dot for extension
SAFE_FILENAME_REGEX = re.compile(r"^[a-zA-Z0-9_\-]+\.(csv|parquet)$")


@router.get("/processed")
async def list_processed_files():
    """Returns a list of all cleaned CSV and Parquet files ready for ML modeling."""
    processed_dir = settings.DATA_PROCESSED_DIR.resolve()
    if not processed_dir.exists():
        return {"files": []}

    files = []
    for f in processed_dir.iterdir():
        if f.suffix in [".csv", ".parquet"]:
            files.append({
                "filename": f.name,
                "format": f.suffix[1:].upper(),
                "size_bytes": f.stat().st_size,
                "modified_at": f.stat().st_mtime,
            })
    return {"files": files}


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
