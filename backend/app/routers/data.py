"""Data Management & File Download Router."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from ..config import settings

router = APIRouter(prefix="/api/data", tags=["Data Artifacts"])


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
    """Safely downloads a cleaned dataset file with path traversal protection."""
    # Prevent path traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename format.")

    file_path = (settings.DATA_PROCESSED_DIR / filename).resolve()
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    # Assert file is within DATA_PROCESSED_DIR
    if settings.DATA_PROCESSED_DIR.resolve() not in file_path.parents:
        raise HTTPException(status_code=403, detail="Access denied: outside directory boundary.")

    media_type = "text/csv" if filename.endswith(".csv") else "application/octet-stream"
    return FileResponse(path=file_path, filename=filename, media_type=media_type)
