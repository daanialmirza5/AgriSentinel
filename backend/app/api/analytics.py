from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import AnalyticsSummaryOut
from app.services import analytics as analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummaryOut)
def summary(field_id: str | None = None, db: Session = Depends(get_db)):
    return analytics_service.summary(db, field_id)


@router.get("/detections")
def detections(field_id: str | None = None, db: Session = Depends(get_db)):
    return {"by_date": analytics_service.detections_over_time(db, field_id)}


@router.get("/targets")
def targets(field_id: str | None = None, db: Session = Depends(get_db)):
    return analytics_service.summary(db, field_id)["target_status_distribution"]


@router.get("/trends")
def trends(field_id: str | None = None, db: Session = Depends(get_db)):
    return {"detections_by_date": analytics_service.detections_over_time(db, field_id)}
