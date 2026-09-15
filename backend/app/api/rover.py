from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Field, RoverEvent, RoverSession, Target
from app.schemas import RoverEventOut, RoverNavigateRequest, RoverStartRequest, RoverStatusOut
from app.services import rover_simulator as rs

router = APIRouter(prefix="/rover", tags=["rover"])


def _status_out(session: RoverSession, message: str | None = None) -> RoverStatusOut:
    path_preview: list[list[float]] = []
    if session.status == "NAVIGATING" and session.current_target_id:
        pass  # frontend derives destination from the target's field coordinates
    return RoverStatusOut(
        id=session.id,
        field_id=session.field_id,
        status=session.status,
        position_x=session.position_x,
        position_y=session.position_y,
        heading_deg=session.heading_deg,
        speed_mps=session.speed_mps,
        safety_state=session.safety_state,
        current_target_id=session.current_target_id,
        path_preview=path_preview,
        mode=session.mode,
        message=message,
    )


def _get_or_404(db: Session, field_id: str) -> RoverSession:
    session = rs.get_active_session(db, field_id)
    if not session:
        raise HTTPException(404, "No active rover session for this field. Start one first.")
    return session


@router.post("/simulation/start", response_model=RoverStatusOut)
def start(payload: RoverStartRequest, db: Session = Depends(get_db)):
    field = db.query(Field).get(payload.field_id)
    if not field:
        raise HTTPException(404, "Field not found")
    session = rs.start_session(db, field)
    return _status_out(session)


@router.post("/simulation/pause", response_model=RoverStatusOut)
def pause(field_id: str, db: Session = Depends(get_db)):
    session = _get_or_404(db, field_id)
    session = rs.pause(db, session)
    return _status_out(session)


@router.post("/simulation/resume", response_model=RoverStatusOut)
def resume(field_id: str, db: Session = Depends(get_db)):
    session = _get_or_404(db, field_id)
    session = rs.resume(db, session)
    return _status_out(session)


@router.post("/simulation/stop", response_model=RoverStatusOut)
def stop(field_id: str, db: Session = Depends(get_db)):
    session = _get_or_404(db, field_id)
    session = rs.stop(db, session)
    return _status_out(session)


@router.post("/emergency-stop", response_model=RoverStatusOut)
def emergency_stop(field_id: str, db: Session = Depends(get_db)):
    session = _get_or_404(db, field_id)
    session = rs.emergency_stop(db, session)
    return _status_out(session, message="EMERGENCY STOP ENGAGED. Reset required before further movement.")


@router.post("/reset", response_model=RoverStatusOut)
def reset(field_id: str, db: Session = Depends(get_db)):
    session = _get_or_404(db, field_id)
    session = rs.reset(db, session)
    return _status_out(session)


@router.get("/status", response_model=RoverStatusOut)
def status(field_id: str, db: Session = Depends(get_db)):
    session = rs.get_active_session(db, field_id)
    if not session:
        return RoverStatusOut(status="NO_SESSION", message="No rover session started for this field yet.")
    session = rs.sync(db, session)
    return _status_out(session)


@router.post("/navigate", response_model=RoverStatusOut)
def navigate(payload: RoverNavigateRequest, db: Session = Depends(get_db)):
    target = db.query(Target).options(joinedload(Target.detection)).filter(Target.id == payload.target_id).first()
    if not target:
        raise HTTPException(404, "Target not found")
    session = rs.get_active_session(db, target.field_id)
    if not session:
        raise HTTPException(400, "No active rover session for this target's field. Start one first.")
    if session.safety_state == "ESTOP":
        raise HTTPException(409, "Rover is in emergency-stop safety lock. Reset before navigating.")
    try:
        session = rs.navigate_to_target(db, session, target)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    target.status = "NAVIGATING"
    db.commit()
    return _status_out(session)


@router.post("/return-to-start", response_model=RoverStatusOut)
def return_to_start(field_id: str, db: Session = Depends(get_db)):
    session = _get_or_404(db, field_id)
    if session.safety_state == "ESTOP":
        raise HTTPException(409, "Rover is in emergency-stop safety lock. Reset before navigating.")
    session = rs.return_to_start(db, session)
    return _status_out(session)


@router.get("/events", response_model=list[RoverEventOut])
def events(field_id: str, limit: int = 50, db: Session = Depends(get_db)):
    session = rs.get_active_session(db, field_id)
    if not session:
        return []
    return (
        db.query(RoverEvent)
        .filter(RoverEvent.rover_session_id == session.id)
        .order_by(RoverEvent.timestamp.desc())
        .limit(limit)
        .all()
    )
