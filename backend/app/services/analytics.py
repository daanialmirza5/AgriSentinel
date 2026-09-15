from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Detection, Inspection, Intervention, Target


def summary(db: Session, field_id: str | None = None) -> dict:
    insp_q = db.query(Inspection)
    det_q = db.query(Detection).join(Inspection)
    tgt_q = db.query(Target)
    if field_id:
        insp_q = insp_q.filter(Inspection.field_id == field_id)
        det_q = det_q.filter(Inspection.field_id == field_id)
        tgt_q = tgt_q.filter(Target.field_id == field_id)

    total_inspections = insp_q.count()
    total_detections = det_q.count()

    by_type_rows = det_q.with_entities(Detection.target_type, func.count(Detection.id)).group_by(Detection.target_type).all()
    detections_by_target_type = {t: c for t, c in by_type_rows}

    avg_conf = det_q.with_entities(func.avg(Detection.confidence)).scalar()
    avg_time = insp_q.with_entities(func.avg(Inspection.processing_time_ms)).scalar()

    total_targets = tgt_q.count()
    pending_targets = tgt_q.filter(
        Target.status.in_(["DETECTED", "REVIEW_REQUIRED", "SELECTED", "PLANNED", "NAVIGATING", "ARRIVED", "INTERVENTION_PENDING"])
    ).count()

    status_rows = tgt_q.with_entities(Target.status, func.count(Target.id)).group_by(Target.status).all()
    target_status_distribution = {s: c for s, c in status_rows}

    completed_interventions_q = db.query(Intervention).filter(Intervention.status == "COMPLETED")
    if field_id:
        completed_interventions_q = completed_interventions_q.join(Target).filter(Target.field_id == field_id)
    completed_interventions = completed_interventions_q.count()

    last_inspection = insp_q.order_by(Inspection.created_at.desc()).first()

    return {
        "total_inspections": total_inspections,
        "total_detections": total_detections,
        "detections_by_target_type": detections_by_target_type,
        "average_confidence": round(avg_conf, 4) if avg_conf is not None else None,
        "average_inference_time_ms": round(avg_time, 2) if avg_time is not None else None,
        "total_targets": total_targets,
        "pending_targets": pending_targets,
        "completed_interventions": completed_interventions,
        "target_status_distribution": target_status_distribution,
        "last_inspection_at": last_inspection.created_at if last_inspection else None,
    }


def detections_over_time(db: Session, field_id: str | None = None) -> list[dict]:
    q = db.query(func.date(Inspection.created_at), func.sum(Inspection.detection_count)).group_by(func.date(Inspection.created_at))
    if field_id:
        q = q.filter(Inspection.field_id == field_id)
    return [{"date": str(d), "count": int(c or 0)} for d, c in q.order_by(func.date(Inspection.created_at)).all()]
