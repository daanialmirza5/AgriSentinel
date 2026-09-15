from __future__ import annotations

import time

import cv2
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import RESULTS_DIR, UPLOADS_DIR
from app.database import get_db
from app.models import Field, Inspection
from app.schemas import CameraStartRequest, CameraStatusOut, InspectionDetail
from app.services import settings_store
from app.services.camera_manager import camera_manager
from app.services.inference import inference_service
from app.services.preprocessing import resize_max_dim
from app.api.inspections import _persist_detections

router = APIRouter(prefix="/camera", tags=["camera"])


@router.get("/devices")
def list_devices():
    return {"devices": camera_manager.list_devices()}


@router.post("/start", response_model=CameraStatusOut)
def start_camera(payload: CameraStartRequest):
    status = camera_manager.start(payload.device_index, payload.field_id)
    return status


@router.post("/stop", response_model=CameraStatusOut)
def stop_camera():
    return camera_manager.stop()


@router.get("/status", response_model=CameraStatusOut)
def camera_status():
    return camera_manager.status()


@router.get("/stream")
def camera_stream():
    if not camera_manager.active:
        raise HTTPException(400, "Camera is not active. Call /api/camera/start first.")
    return StreamingResponse(camera_manager.mjpeg_generator(), media_type="multipart/x-mixed-replace; boundary=frame")


@router.post("/capture", response_model=InspectionDetail)
def capture_inspection(field_id: str, db: Session = Depends(get_db)):
    if not camera_manager.active:
        raise HTTPException(400, "Camera is not active.")
    frame = camera_manager.capture_raw_frame()
    if frame is None:
        raise HTTPException(400, "No frame available yet.")
    field = db.query(Field).get(field_id)
    if not field:
        raise HTTPException(404, "Field not found")

    frame = resize_max_dim(frame)
    settings = settings_store.get_all(db)
    conf = settings["confidence_threshold"]
    force_classical = settings["detection_backend_preference"] == "classical"

    fname = f"camera_capture_{int(time.time())}.jpg"
    cv2.imwrite(str(UPLOADS_DIR / fname), frame)

    detections, annotated, meta = inference_service.infer(frame, conf_threshold=conf, force_classical=force_classical)
    annotated_name = f"annotated_{fname}"
    cv2.imwrite(str(RESULTS_DIR / annotated_name), annotated)

    inspection = Inspection(
        field_id=field.id,
        source_type="camera",
        original_filename=fname,
        original_asset_path=f"/media/uploads/{fname}",
        annotated_asset_path=f"/media/results/{annotated_name}",
        model_name=meta["model_name"],
        model_version=meta["model_version"],
        detection_mode=meta["detection_mode"],
        status="completed",
        detection_count=len(detections),
        processing_time_ms=meta["processing_time_ms"],
    )
    db.add(inspection)
    db.flush()
    h, w = frame.shape[:2]
    _persist_detections(db, inspection, field, detections, w, h)
    db.commit()
    db.refresh(inspection)
    return inspection
