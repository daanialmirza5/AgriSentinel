from __future__ import annotations

import re
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.config import ALLOWED_IMAGE_EXT, ALLOWED_VIDEO_EXT, MAX_UPLOAD_BYTES

_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9_.-]+")


def safe_filename(original: str) -> str:
    stem = Path(original or "upload").stem
    ext = Path(original or "").suffix.lower()
    stem = _SAFE_NAME_RE.sub("_", stem)[:60] or "upload"
    return f"{stem}_{uuid.uuid4().hex[:8]}{ext}"


def validate_extension(filename: str, allowed: set[str]) -> str:
    ext = Path(filename or "").suffix.lower()
    if ext not in allowed:
        raise HTTPException(400, f"Unsupported file extension '{ext}'. Allowed: {sorted(allowed)}")
    return ext


async def read_upload(file: UploadFile, allowed: set[str]) -> tuple[bytes, str]:
    validate_extension(file.filename or "", allowed)
    data = await file.read()
    if len(data) == 0:
        raise HTTPException(400, "Uploaded file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(400, f"File too large. Max {MAX_UPLOAD_BYTES // (1024*1024)} MB.")
    return data, safe_filename(file.filename or "upload")


def within_directory(path: Path, directory: Path) -> bool:
    try:
        path.resolve().relative_to(directory.resolve())
        return True
    except ValueError:
        return False
