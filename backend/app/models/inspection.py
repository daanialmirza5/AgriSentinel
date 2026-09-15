from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return uuid.uuid4().hex


class Inspection(Base):
    __tablename__ = "inspections"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    session_id: Mapped[str | None] = mapped_column(ForeignKey("monitoring_sessions.id"), nullable=True, index=True)
    field_id: Mapped[str] = mapped_column(ForeignKey("fields.id"), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(32), default="image")  # image|video|camera
    original_filename: Mapped[str] = mapped_column(String(255), default="")
    original_asset_path: Mapped[str] = mapped_column(String(500), default="")
    annotated_asset_path: Mapped[str] = mapped_column(String(500), default="")
    model_name: Mapped[str] = mapped_column(String(120), default="unavailable")
    model_version: Mapped[str] = mapped_column(String(60), default="n/a")
    detection_mode: Mapped[str] = mapped_column(String(40), default="model_unavailable")
    status: Mapped[str] = mapped_column(String(32), default="completed")  # completed|failed|processing
    detection_count: Mapped[int] = mapped_column(Integer, default=0)
    processing_time_ms: Mapped[float] = mapped_column(Float, default=0.0)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow, index=True)

    field = relationship("Field", back_populates="inspections")
    session = relationship("MonitoringSession", back_populates="inspections")
    detections = relationship("Detection", back_populates="inspection", cascade="all, delete-orphan")
