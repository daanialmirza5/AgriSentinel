from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import JSON, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return uuid.uuid4().hex


class Field(Base):
    __tablename__ = "fields"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    crop_type: Mapped[str] = mapped_column(String(80), default="unspecified")
    width_m: Mapped[float] = mapped_column(Float, nullable=False)
    length_m: Mapped[float] = mapped_column(Float, nullable=False)
    row_spacing_m: Mapped[float] = mapped_column(Float, default=0.5)
    row_direction_deg: Mapped[float] = mapped_column(Float, default=0.0)
    configuration: Mapped[dict] = mapped_column(JSON, default=dict)
    # configuration holds: restricted_zones, obstacles, rover_start {x,y}, max_speed, is_demo
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow
    )

    inspections = relationship("Inspection", back_populates="field", cascade="all, delete-orphan")
    targets = relationship("Target", back_populates="field", cascade="all, delete-orphan")
    rover_sessions = relationship("RoverSession", back_populates="field", cascade="all, delete-orphan")
