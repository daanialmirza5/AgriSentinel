"""Pydantic request/response schemas for the AgriSentinel API."""
from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field as PydField


# ---------------------------------------------------------------------------
# Fields
# ---------------------------------------------------------------------------
class FieldCreate(BaseModel):
    name: str
    crop_type: str = "unspecified"
    width_m: float = PydField(gt=0)
    length_m: float = PydField(gt=0)
    row_spacing_m: float = 0.5
    row_direction_deg: float = 0.0
    configuration: dict[str, Any] = PydField(default_factory=dict)


class FieldUpdate(BaseModel):
    name: Optional[str] = None
    crop_type: Optional[str] = None
    width_m: Optional[float] = None
    length_m: Optional[float] = None
    row_spacing_m: Optional[float] = None
    row_direction_deg: Optional[float] = None
    configuration: Optional[dict[str, Any]] = None


class FieldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    crop_type: str
    width_m: float
    length_m: float
    row_spacing_m: float
    row_direction_deg: float
    configuration: dict[str, Any]
    created_at: dt.datetime
    updated_at: dt.datetime


# ---------------------------------------------------------------------------
# Detections / Inspections
# ---------------------------------------------------------------------------
class BBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class DetectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    inspection_id: str
    class_id: int
    class_name: str
    target_type: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float
    centroid_x: float
    centroid_y: float
    field_x: Optional[float]
    field_y: Optional[float]
    localization_confidence: str
    localization_method: str


class InspectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    session_id: Optional[str]
    field_id: str
    source_type: str
    original_filename: str
    original_asset_path: str
    annotated_asset_path: str
    model_name: str
    model_version: str
    detection_mode: str
    status: str
    detection_count: int
    processing_time_ms: float
    error_message: Optional[str]
    created_at: dt.datetime


class InspectionDetail(InspectionOut):
    detections: list[DetectionOut] = PydField(default_factory=list)


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------
class TargetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    detection_id: str
    field_id: str
    status: str
    priority_score: float
    priority_explanation: str
    notes: str
    operator_approved: bool
    created_at: dt.datetime
    selected_at: Optional[dt.datetime]
    completed_at: Optional[dt.datetime]


class TargetDetail(TargetOut):
    detection: DetectionOut


class TargetUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    operator_approved: Optional[bool] = None


class TargetNote(BaseModel):
    notes: str


# ---------------------------------------------------------------------------
# Rover
# ---------------------------------------------------------------------------
class RoverStatusOut(BaseModel):
    id: Optional[str] = None
    field_id: Optional[str] = None
    status: str
    position_x: float = 0.0
    position_y: float = 0.0
    heading_deg: float = 0.0
    speed_mps: float = 0.0
    safety_state: str = "NORMAL"
    current_target_id: Optional[str] = None
    path_preview: list[list[float]] = PydField(default_factory=list)
    mode: str = "simulation"
    message: Optional[str] = None


class RoverStartRequest(BaseModel):
    field_id: str


class RoverNavigateRequest(BaseModel):
    target_id: str


class RoverEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    event_type: str
    payload: dict[str, Any]
    timestamp: dt.datetime


# ---------------------------------------------------------------------------
# Actuator
# ---------------------------------------------------------------------------
class ActuatorSimulateRequest(BaseModel):
    target_id: str
    operator_approved: bool = False


class ActuatorResultOut(BaseModel):
    success: bool
    status: str
    message: str
    safety_checks: dict[str, Any]
    intervention_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
class AnalyticsSummaryOut(BaseModel):
    total_inspections: int
    total_detections: int
    detections_by_target_type: dict[str, int]
    average_confidence: Optional[float]
    average_inference_time_ms: Optional[float]
    total_targets: int
    pending_targets: int
    completed_interventions: int
    target_status_distribution: dict[str, int]
    last_inspection_at: Optional[dt.datetime]


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
class SettingsOut(BaseModel):
    values: dict[str, Any]
    model_status: dict[str, Any]


class SettingsUpdate(BaseModel):
    values: dict[str, Any]


# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
class CameraStartRequest(BaseModel):
    device_index: int = 0
    field_id: Optional[str] = None


class CameraStatusOut(BaseModel):
    active: bool
    device_index: Optional[int]
    available: bool
    frames_processed: int
    last_detection_count: int
    error: Optional[str] = None
