from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.config import DEFAULT_CONFIDENCE_THRESHOLD
from app.models import SettingRecord

DEFAULTS: dict[str, Any] = {
    "confidence_threshold": DEFAULT_CONFIDENCE_THRESHOLD,
    "detection_backend_preference": "auto",  # auto|yolo|classical
    "rover_speed_mps": 1.2,
    "simulation_speed_multiplier": 1.0,
    "arrival_tolerance_m": 0.2,
    "require_operator_approval": True,
    "camera_default_index": 0,
}

_TYPES = {
    "confidence_threshold": float,
    "rover_speed_mps": float,
    "simulation_speed_multiplier": float,
    "arrival_tolerance_m": float,
    "require_operator_approval": bool,
    "camera_default_index": int,
    "detection_backend_preference": str,
}


def _coerce(key: str, raw: str) -> Any:
    t = _TYPES.get(key, str)
    if t is bool:
        return raw.lower() == "true"
    if t is float:
        return float(raw)
    if t is int:
        return int(raw)
    return raw


def get_all(db: Session) -> dict[str, Any]:
    values = dict(DEFAULTS)
    for row in db.query(SettingRecord).all():
        try:
            values[row.key] = _coerce(row.key, row.value)
        except (ValueError, TypeError):
            continue
    return values


def update(db: Session, values: dict[str, Any]) -> dict[str, Any]:
    for key, val in values.items():
        row = db.query(SettingRecord).filter(SettingRecord.key == key).first()
        str_val = json.dumps(val) if isinstance(val, (dict, list)) else str(val)
        if row is None:
            row = SettingRecord(key=key, value=str_val, value_type=type(val).__name__)
            db.add(row)
        else:
            row.value = str_val
            row.value_type = type(val).__name__
    db.commit()
    return get_all(db)
