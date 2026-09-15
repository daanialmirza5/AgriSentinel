from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return uuid.uuid4().hex


class Target(Base):
    __tablename__ = "targets"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    detection_id: Mapped[str] = mapped_column(ForeignKey("detections.id"), nullable=False, unique=True)
    field_id: Mapped[str] = mapped_column(ForeignKey("fields.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="DETECTED", index=True)
    priority_score: Mapped[float] = mapped_column(Float, default=0.0)
    priority_explanation: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    operator_approved: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow, index=True)
    selected_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)

    detection = relationship("Detection", back_populates="target")
    field = relationship("Field", back_populates="targets")
    interventions = relationship("Intervention", back_populates="target", cascade="all, delete-orphan")


TARGET_STATUSES = [
    "DETECTED",
    "REVIEW_REQUIRED",
    "SELECTED",
    "PLANNED",
    "NAVIGATING",
    "ARRIVED",
    "INTERVENTION_PENDING",
    "COMPLETED",
    "SKIPPED",
    "BLOCKED",
    "INVALID",
]
