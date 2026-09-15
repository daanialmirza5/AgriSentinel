from __future__ import annotations

import datetime as dt

from fastapi import APIRouter
from sqlalchemy import text

from app.database import SessionLocal
from app.services.camera_manager import camera_manager
from app.services.inference import inference_service

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    db_ok = True
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "database_ok": db_ok, "timestamp": dt.datetime.utcnow().isoformat()}


@router.get("/model/status")
def model_status():
    s = inference_service.status
    return {
        "backend": s.backend,
        "installed": s.installed,
        "loaded": s.loaded,
        "is_generic_demo": s.is_generic_demo,
        "model_path": s.model_path,
        "model_filename": s.model_filename,
        "model_format": s.model_format,
        "task": s.task,
        "version": s.version,
        "device": s.device,
        "error": s.error,
        "label": s.label,
        "warning": s.warning,
    }


@router.post("/model/reload")
def reload_model():
    inference_service.reload()
    return model_status()


@router.get("/system/status")
def system_status():
    return {
        "model": model_status(),
        "camera": camera_manager.status(),
        "timestamp": dt.datetime.utcnow().isoformat(),
    }
