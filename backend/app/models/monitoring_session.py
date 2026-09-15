from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return uuid.uuid4().hex


class MonitoringSession(Base):
    __tablename__ = "monitoring_sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    field_id: Mapped[str] = mapped_column(ForeignKey("fields.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    source_type: Mapped[str] = mapped_column(String(32), default="image")  # image|video|camera
    started_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    ended_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    model_name: Mapped[str] = mapped_column(String(120), default="unavailable")
    model_version: Mapped[str] = mapped_column(String(60), default="n/a")

    inspections = relationship("Inspection", back_populates="session")
