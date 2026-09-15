from __future__ import annotations

import csv
import io

from sqlalchemy.orm import Session

from app.models import Detection, Inspection, Intervention, Target


def inspections_csv(db: Session) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "field_id", "source_type", "status", "detection_mode", "detection_count", "processing_time_ms", "created_at"])
    for i in db.query(Inspection).order_by(Inspection.created_at.desc()).all():
        w.writerow([i.id, i.field_id, i.source_type, i.status, i.detection_mode, i.detection_count, i.processing_time_ms, i.created_at])
    return buf.getvalue()


def targets_csv(db: Session) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "field_id", "status", "priority_score", "operator_approved", "created_at", "completed_at"])
    for t in db.query(Target).order_by(Target.created_at.desc()).all():
        w.writerow([t.id, t.field_id, t.status, t.priority_score, t.operator_approved, t.created_at, t.completed_at])
    return buf.getvalue()


def interventions_csv(db: Session) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "target_id", "action_type", "mode", "status", "operator_approved", "started_at", "completed_at", "failure_reason"])
    for iv in db.query(Intervention).order_by(Intervention.started_at.desc()).all():
        w.writerow([iv.id, iv.target_id, iv.action_type, iv.mode, iv.status, iv.operator_approved, iv.started_at, iv.completed_at, iv.failure_reason])
    return buf.getvalue()
