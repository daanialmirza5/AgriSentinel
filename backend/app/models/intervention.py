from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return uuid.uuid4().hex


class Intervention(Base):
    __tablename__ = "interventions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    target_id: Mapped[str] = mapped_column(ForeignKey("targets.id"), nullable=False, index=True)
    rover_session_id: Mapped[str | None] = mapped_column(ForeignKey("rover_sessions.id"), nullable=True)
    action_type: Mapped[str] = mapped_column(String(40), default="simulated_marker")
    mode: Mapped[str] = mapped_column(String(20), default="simulation")
    status: Mapped[str] = mapped_column(String(32), default="PENDING")  # PENDING|COMPLETED|FAILED|BLOCKED
    safety_checks: Mapped[dict] = mapped_column(JSON, default=dict)
    operator_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(300), nullable=True)

    target = relationship("Target", back_populates="interventions")
