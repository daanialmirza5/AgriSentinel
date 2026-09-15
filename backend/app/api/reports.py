from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import reports as reports_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/inspections.csv")
def inspections_csv(db: Session = Depends(get_db)):
    return PlainTextResponse(reports_service.inspections_csv(db), media_type="text/csv")


@router.get("/targets.csv")
def targets_csv(db: Session = Depends(get_db)):
    return PlainTextResponse(reports_service.targets_csv(db), media_type="text/csv")


@router.get("/interventions.csv")
def interventions_csv(db: Session = Depends(get_db)):
    return PlainTextResponse(reports_service.interventions_csv(db), media_type="text/csv")
