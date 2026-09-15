from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Target
from app.schemas import TargetDetail, TargetNote, TargetOut, TargetUpdate

router = APIRouter(prefix="/targets", tags=["targets"])


def _q(db: Session):
    return db.query(Target).options(joinedload(Target.detection))


@router.get("", response_model=list[TargetDetail])
def list_targets(field_id: str | None = None, status: str | None = None, db: Session = Depends(get_db)):
    q = _q(db)
    if field_id:
        q = q.filter(Target.field_id == field_id)
    if status:
        q = q.filter(Target.status == status)
    return q.order_by(Target.priority_score.desc()).all()


@router.get("/{target_id}", response_model=TargetDetail)
def get_target(target_id: str, db: Session = Depends(get_db)):
    target = _q(db).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(404, "Target not found")
    return target


@router.patch("/{target_id}", response_model=TargetDetail)
def update_target(target_id: str, payload: TargetUpdate, db: Session = Depends(get_db)):
    target = _q(db).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(404, "Target not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(target, k, v)
    db.commit()
    db.refresh(target)
    return target


@router.post("/{target_id}/approve", response_model=TargetDetail)
def approve_target(target_id: str, db: Session = Depends(get_db)):
    target = _q(db).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(404, "Target not found")
    target.operator_approved = True
    target.status = "SELECTED"
    target.selected_at = dt.datetime.utcnow()
    db.commit()
    db.refresh(target)
    return target


@router.post("/{target_id}/skip", response_model=TargetDetail)
def skip_target(target_id: str, db: Session = Depends(get_db)):
    target = _q(db).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(404, "Target not found")
    target.status = "SKIPPED"
    db.commit()
    db.refresh(target)
    return target


@router.post("/{target_id}/plan", response_model=TargetDetail)
def plan_target(target_id: str, db: Session = Depends(get_db)):
    target = _q(db).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(404, "Target not found")
    if target.status not in ("SELECTED", "DETECTED", "REVIEW_REQUIRED"):
        raise HTTPException(400, f"Cannot plan a target in status {target.status}")
    target.status = "PLANNED"
    db.commit()
    db.refresh(target)
    return target


@router.post("/{target_id}/note", response_model=TargetDetail)
def note_target(target_id: str, payload: TargetNote, db: Session = Depends(get_db)):
    target = _q(db).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(404, "Target not found")
    target.notes = payload.notes
    db.commit()
    db.refresh(target)
    return target
