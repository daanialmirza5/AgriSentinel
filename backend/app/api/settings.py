from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import SettingsOut, SettingsUpdate
from app.services import settings_store
from app.services.inference import inference_service

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
def get_settings(db: Session = Depends(get_db)):
    s = inference_service.status
    return SettingsOut(
        values=settings_store.get_all(db),
        model_status={"backend": s.backend, "label": s.label, "loaded": s.loaded, "warning": s.warning},
    )


@router.patch("", response_model=SettingsOut)
def patch_settings(payload: SettingsUpdate, db: Session = Depends(get_db)):
    settings_store.update(db, payload.values)
    return get_settings(db)
