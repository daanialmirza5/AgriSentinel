from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return uuid.uuid4().hex


class Detection(Base):
    __tablename__ = "detections"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    inspection_id: Mapped[str] = mapped_column(ForeignKey("inspections.id"), nullable=False, index=True)
    class_id: Mapped[int] = mapped_column(Integer, default=-1)
    class_name: Mapped[str] = mapped_column(String(80), default="unknown")
    target_type: Mapped[str] = mapped_column(String(40), default="unclassified")  # weed|crop|unclassified_vegetation|generic_object
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    x1: Mapped[float] = mapped_column(Float, default=0.0)
    y1: Mapped[float] = mapped_column(Float, default=0.0)
    x2: Mapped[float] = mapped_column(Float, default=0.0)
    y2: Mapped[float] = mapped_column(Float, default=0.0)
    mask_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    centroid_x: Mapped[float] = mapped_column(Float, default=0.0)
    centroid_y: Mapped[float] = mapped_column(Float, default=0.0)
    field_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    field_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    localization_confidence: Mapped[str] = mapped_column(String(20), default="approximate")  # approximate|unavailable
    localization_method: Mapped[str] = mapped_column(String(60), default="simulated_ground_plane")

    inspection = relationship("Inspection", back_populates="detections")
    target = relationship("Target", back_populates="detection", uselist=False, cascade="all, delete-orphan")
