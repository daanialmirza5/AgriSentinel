from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Intervention, RoverEvent, Target
from app.schemas import ActuatorResultOut, ActuatorSimulateRequest
from app.services import rover_simulator as rs
from app.services import settings_store
from app.services.actuator import ActuatorTarget, simulated_actuator
from app.services.safety import evaluate_target_safety, in_any_zone

router = APIRouter(prefix="/actuator", tags=["actuator"])


@router.get("/status")
def actuator_status():
    return {"backend": "SimulatedActuator", "stopped": simulated_actuator._stopped, "note": "Virtual marker only. No physical actuator is connected."}


@router.post("/stop")
def actuator_stop():
    simulated_actuator.stop()
    return {"stopped": True}


@router.post("/simulate", response_model=ActuatorResultOut)
def actuator_simulate(payload: ActuatorSimulateRequest, db: Session = Depends(get_db)):
    target = db.query(Target).options(joinedload(Target.detection)).filter(Target.id == payload.target_id).first()
    if not target:
        raise HTTPException(404, "Target not found")

    field = target.field
    detection = target.detection
    session = rs.get_active_session(db, target.field_id)
    settings = settings_store.get_all(db)

    restricted = (field.configuration or {}).get("restricted_zones", [])
    crop_zones = (field.configuration or {}).get("crop_protection_zones", [])
    in_restricted = detection.field_x is not None and in_any_zone(detection.field_x, detection.field_y, restricted)
    in_crop_zone = detection.field_x is not None and in_any_zone(detection.field_x, detection.field_y, crop_zones)

    check = evaluate_target_safety(
        confidence=detection.confidence,
        localization_confidence=detection.localization_confidence,
        in_restricted_zone=in_restricted,
        in_crop_protection_zone=in_crop_zone,
        rover_speed_mps=session.speed_mps if session else 0.0,
        emergency_stop_active=bool(session and session.safety_state == "ESTOP"),
        operator_approved=payload.operator_approved or target.operator_approved,
        require_operator_approval=settings["require_operator_approval"],
    )

    intervention = Intervention(
        target_id=target.id,
        rover_session_id=session.id if session else None,
        action_type="simulated_marker",
        mode="simulation",
        status="PENDING",
        safety_checks=check.checks,
        operator_approved=payload.operator_approved or target.operator_approved,
    )
    db.add(intervention)
    db.flush()

    if not check.passed:
        intervention.status = "BLOCKED"
        intervention.failure_reason = "Safety checks failed: " + ", ".join(check.reasons)
        target.status = "BLOCKED"
        db.commit()
        return ActuatorResultOut(
            success=False,
            status="BLOCKED",
            message=intervention.failure_reason,
            safety_checks=check.checks,
            intervention_id=intervention.id,
        )

    result = simulated_actuator.execute(ActuatorTarget(target_id=target.id, field_x=detection.field_x, field_y=detection.field_y))
    if not result.get("success"):
        intervention.status = "FAILED"
        intervention.failure_reason = result.get("reason", "actuator failure")
        db.commit()
        return ActuatorResultOut(
            success=False, status="FAILED", message=intervention.failure_reason, safety_checks=check.checks, intervention_id=intervention.id
        )

    intervention.status = "COMPLETED"
    intervention.completed_at = dt.datetime.utcnow()
    target.status = "COMPLETED"
    target.completed_at = dt.datetime.utcnow()
    if session:
        session.status = "COMPLETED"
        db.add(RoverEvent(rover_session_id=session.id, event_type="intervention_simulated", payload={"target_id": target.id}))
    db.commit()

    return ActuatorResultOut(
        success=True,
        status="COMPLETED",
        message="Simulated intervention completed. No physical treatment was applied.",
        safety_checks=check.checks,
        intervention_id=intervention.id,
    )
