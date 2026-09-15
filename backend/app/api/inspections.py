from __future__ import annotations

import time

import cv2
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import ALLOWED_IMAGE_EXT, ALLOWED_VIDEO_EXT, MAX_VIDEO_SAMPLE_FRAMES, RESULTS_DIR, UPLOADS_DIR
from app.database import get_db
from app.models import Detection, Field, Inspection, Target
from app.schemas import InspectionDetail, InspectionOut
from app.services import settings_store, target_planner
from app.services.inference import inference_service
from app.services.localization import pixel_to_field
from app.services.preprocessing import ImageValidationError, load_image_bytes, resize_max_dim
from app.utils.files import read_upload

router = APIRouter(tags=["inspections"])


def _persist_detections(db: Session, inspection: Inspection, field: Field, detections, img_w: int, img_h: int) -> int:
    count = 0
    for d in detections:
        loc = pixel_to_field(d.centroid_x, d.centroid_y, img_w, img_h, field.width_m, field.length_m)
        det = Detection(
            inspection_id=inspection.id,
            class_id=d.class_id,
            class_name=d.class_name,
            target_type=d.target_type,
            confidence=d.confidence,
            x1=d.x1, y1=d.y1, x2=d.x2, y2=d.y2,
            centroid_x=d.centroid_x, centroid_y=d.centroid_y,
            field_x=loc.field_x, field_y=loc.field_y,
            localization_confidence=loc.localization_confidence,
            localization_method=loc.method,
        )
        db.add(det)
        db.flush()

        score, explanation = target_planner.score_target(
            confidence=d.confidence,
            target_type=d.target_type,
            field_x=loc.field_x,
            field_y=loc.field_y,
            field_diag_m=(field.width_m**2 + field.length_m**2) ** 0.5,
        )
        status = "REVIEW_REQUIRED" if d.confidence < 0.5 else "DETECTED"
        db.add(
            Target(
                detection_id=det.id,
                field_id=field.id,
                status=status,
                priority_score=score,
                priority_explanation=explanation,
            )
        )
        count += 1
    return count


@router.post("/inspect/image", response_model=InspectionDetail)
async def inspect_image(field_id: str, file: UploadFile, db: Session = Depends(get_db)):
    field = db.query(Field).get(field_id)
    if not field:
        raise HTTPException(404, "Field not found")

    data, fname = await read_upload(file, ALLOWED_IMAGE_EXT)
    try:
        img = load_image_bytes(data)
    except ImageValidationError as exc:
        raise HTTPException(400, str(exc))
    img = resize_max_dim(img)

    orig_path = UPLOADS_DIR / fname
    orig_path.write_bytes(data)

    settings = settings_store.get_all(db)
    conf = settings["confidence_threshold"]
    force_classical = settings["detection_backend_preference"] == "classical"

    start = time.perf_counter()
    detections, annotated, meta = inference_service.infer(img, conf_threshold=conf, force_classical=force_classical)
    elapsed_ms = (time.perf_counter() - start) * 1000

    annotated_name = f"annotated_{fname}"
    annotated_path = RESULTS_DIR / annotated_name
    cv2.imwrite(str(annotated_path), annotated)

    inspection = Inspection(
        field_id=field.id,
        source_type="image",
        original_filename=file.filename or fname,
        original_asset_path=f"/media/uploads/{fname}",
        annotated_asset_path=f"/media/results/{annotated_name}",
        model_name=meta["model_name"],
        model_version=meta["model_version"],
        detection_mode=meta["detection_mode"],
        status="completed",
        detection_count=len(detections),
        processing_time_ms=elapsed_ms,
    )
    db.add(inspection)
    db.flush()

    h, w = img.shape[:2]
    _persist_detections(db, inspection, field, detections, w, h)
    db.commit()
    db.refresh(inspection)
    return inspection


@router.post("/inspect/video", response_model=InspectionDetail)
async def inspect_video(field_id: str, file: UploadFile, db: Session = Depends(get_db)):
    field = db.query(Field).get(field_id)
    if not field:
        raise HTTPException(404, "Field not found")

    data, fname = await read_upload(file, ALLOWED_VIDEO_EXT)
    orig_path = UPLOADS_DIR / fname
    orig_path.write_bytes(data)

    cap = cv2.VideoCapture(str(orig_path))
    if not cap.isOpened():
        raise HTTPException(400, "Could not open uploaded video file.")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    sample_count = min(MAX_VIDEO_SAMPLE_FRAMES, max(1, total_frames))
    sample_indices = sorted({int(i * total_frames / sample_count) for i in range(sample_count)}) if total_frames else [0]

    settings = settings_store.get_all(db)
    conf = settings["confidence_threshold"]
    force_classical = settings["detection_backend_preference"] == "classical"

    inspection = Inspection(
        field_id=field.id,
        source_type="video",
        original_filename=file.filename or fname,
        original_asset_path=f"/media/uploads/{fname}",
        annotated_asset_path="",
        status="completed",
        detection_mode="pending",
    )
    db.add(inspection)
    db.flush()

    start = time.perf_counter()
    best_frame_path = ""
    best_count = -1
    total_detections = 0
    model_name = model_version = mode = ""

    for idx in sample_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok:
            continue
        frame = resize_max_dim(frame)
        detections, annotated, meta = inference_service.infer(frame, conf_threshold=conf, force_classical=force_classical)
        model_name, model_version, mode = meta["model_name"], meta["model_version"], meta["detection_mode"]
        h, w = frame.shape[:2]
        total_detections += _persist_detections(db, inspection, field, detections, w, h)

        if len(detections) > best_count:
            best_count = len(detections)
            annotated_name = f"annotated_frame_{idx}_{fname}.jpg"
            annotated_path = RESULTS_DIR / annotated_name
            cv2.imwrite(str(annotated_path), annotated)
            best_frame_path = f"/media/results/{annotated_name}"

    cap.release()
    elapsed_ms = (time.perf_counter() - start) * 1000

    inspection.annotated_asset_path = best_frame_path
    inspection.model_name = model_name or "n/a"
    inspection.model_version = model_version or "n/a"
    inspection.detection_mode = mode or "model_unavailable"
    inspection.detection_count = total_detections
    inspection.processing_time_ms = elapsed_ms
    inspection.error_message = (
        f"Sampled {len(sample_indices)} of {total_frames} frames for CPU-bounded processing time. "
        "Best-detection frame shown as annotated preview." if total_frames else None
    )
    db.commit()
    db.refresh(inspection)
    return inspection


@router.get("/inspections", response_model=list[InspectionOut])
def list_inspections(field_id: str | None = None, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    q = db.query(Inspection)
    if field_id:
        q = q.filter(Inspection.field_id == field_id)
    return q.order_by(Inspection.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/inspections/{inspection_id}", response_model=InspectionDetail)
def get_inspection(inspection_id: str, db: Session = Depends(get_db)):
    inspection = db.query(Inspection).get(inspection_id)
    if not inspection:
        raise HTTPException(404, "Inspection not found")
    return inspection


@router.delete("/inspections/{inspection_id}", status_code=204)
def delete_inspection(inspection_id: str, db: Session = Depends(get_db)):
    inspection = db.query(Inspection).get(inspection_id)
    if not inspection:
        raise HTTPException(404, "Inspection not found")
    db.delete(inspection)
    db.commit()
    return None
