from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Field
from app.schemas import FieldCreate, FieldOut, FieldUpdate

router = APIRouter(prefix="/fields", tags=["fields"])


@router.get("", response_model=list[FieldOut])
def list_fields(db: Session = Depends(get_db)):
    return db.query(Field).order_by(Field.created_at.desc()).all()


@router.post("", response_model=FieldOut, status_code=201)
def create_field(payload: FieldCreate, db: Session = Depends(get_db)):
    field = Field(**payload.model_dump())
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


@router.get("/{field_id}", response_model=FieldOut)
def get_field(field_id: str, db: Session = Depends(get_db)):
    field = db.query(Field).get(field_id)
    if not field:
        raise HTTPException(404, "Field not found")
    return field


@router.patch("/{field_id}", response_model=FieldOut)
def update_field(field_id: str, payload: FieldUpdate, db: Session = Depends(get_db)):
    field = db.query(Field).get(field_id)
    if not field:
        raise HTTPException(404, "Field not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(field, k, v)
    db.commit()
    db.refresh(field)
    return field


@router.delete("/{field_id}", status_code=204)
def delete_field(field_id: str, db: Session = Depends(get_db)):
    field = db.query(Field).get(field_id)
    if not field:
        raise HTTPException(404, "Field not found")
    db.delete(field)
    db.commit()
    return None
