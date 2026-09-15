from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return uuid.uuid4().hex


class RoverSession(Base):
    __tablename__ = "rover_sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    field_id: Mapped[str] = mapped_column(ForeignKey("fields.id"), nullable=False, index=True)
    mode: Mapped[str] = mapped_column(String(20), default="simulation")  # simulation|hardware (hardware unused in MVP)
    status: Mapped[str] = mapped_column(String(32), default="IDLE", index=True)
    position_x: Mapped[float] = mapped_column(Float, default=0.0)
    position_y: Mapped[float] = mapped_column(Float, default=0.0)
    heading_deg: Mapped[float] = mapped_column(Float, default=0.0)
    speed_mps: Mapped[float] = mapped_column(Float, default=0.0)
    safety_state: Mapped[str] = mapped_column(String(20), default="NORMAL")  # NORMAL|ESTOP
    current_target_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    started_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    ended_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)

    field = relationship("Field", back_populates="rover_sessions")
    events = relationship("RoverEvent", back_populates="rover_session", cascade="all, delete-orphan")


class RoverEvent(Base):
    __tablename__ = "rover_events"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    rover_session_id: Mapped[str] = mapped_column(ForeignKey("rover_sessions.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(60), default="info")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    timestamp: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow, index=True)

    rover_session = relationship("RoverSession", back_populates="events")


ROVER_STATES = [
    "IDLE",
    "READY",
    "NAVIGATING",
    "ARRIVED",
    "INTERVENTION_PENDING",
    "INTERVENTING",
    "COMPLETED",
    "PAUSED",
    "STOPPED",
    "SAFETY_LOCK",
    "ERROR",
]
