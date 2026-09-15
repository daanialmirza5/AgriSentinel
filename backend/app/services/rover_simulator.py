"""2D rover simulator.

This is a *simulation* of a rover moving across a virtual representation of
the configured field. It does not control, and is not connected to, any
physical robot. Position is advanced using a "pull" model: whenever the
state is read or acted upon, elapsed wall-clock time since the last update is
used to move the rover toward its current target at a configured speed. This
keeps the implementation simple and robust without a background thread
fighting SQLite for the same connection.

State machine (see PRD PART 10.2):
IDLE -> READY -> NAVIGATING -> ARRIVED -> INTERVENTION_PENDING -> INTERVENTING -> COMPLETED
Also: PAUSED, STOPPED, SAFETY_LOCK, ERROR
"""
from __future__ import annotations

import datetime as dt
import math
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Detection, RoverEvent, RoverSession, Target
from app.services.safety import in_any_zone

DEFAULT_SPEED_MPS = 1.2
ARRIVAL_TOLERANCE_M = 0.2
MAX_TICK_SECONDS = 2.0  # cap catch-up jumps after long idle gaps

# transient per-session state not worth persisting to the DB schema
_last_tick: dict[str, dt.datetime] = {}
_nav_override: dict[str, tuple[float, float, str]] = {}  # session_id -> (x, y, label) e.g. "return_to_start"


def _log(db: Session, session_id: str, event_type: str, payload: dict) -> None:
    db.add(RoverEvent(rover_session_id=session_id, event_type=event_type, payload=payload))


def start_session(db: Session, field, restart: bool = False) -> RoverSession:
    active = (
        db.query(RoverSession)
        .filter(RoverSession.field_id == field.id, RoverSession.ended_at.is_(None))
        .order_by(RoverSession.started_at.desc())
        .first()
    )
    if active and not restart:
        return active
    if active:
        active.ended_at = dt.datetime.utcnow()
        active.status = "STOPPED"

    start_pos = (field.configuration or {}).get("rover_start", {"x": 0.0, "y": 0.0})
    session = RoverSession(
        field_id=field.id,
        status="READY",
        position_x=float(start_pos.get("x", 0.0)),
        position_y=float(start_pos.get("y", 0.0)),
        heading_deg=0.0,
        speed_mps=0.0,
        safety_state="NORMAL",
    )
    db.add(session)
    db.flush()
    _last_tick[session.id] = dt.datetime.utcnow()
    _log(db, session.id, "session_started", {"field_id": field.id, "position": start_pos})
    db.commit()
    db.refresh(session)
    return session


def get_active_session(db: Session, field_id: str) -> Optional[RoverSession]:
    return (
        db.query(RoverSession)
        .filter(RoverSession.field_id == field_id, RoverSession.ended_at.is_(None))
        .order_by(RoverSession.started_at.desc())
        .first()
    )


def navigate_to_target(db: Session, session: RoverSession, target: Target) -> RoverSession:
    detection: Detection = target.detection
    if detection.field_x is None or detection.field_y is None:
        raise ValueError("Target has no valid field location; cannot navigate.")

    field = target.field
    restricted = (field.configuration or {}).get("restricted_zones", [])
    if in_any_zone(detection.field_x, detection.field_y, restricted):
        session.status = "ERROR"
        _log(db, session.id, "navigation_blocked", {"reason": "target_in_restricted_zone", "target_id": target.id})
        db.commit()
        db.refresh(session)
        return session

    session.current_target_id = target.id
    session.status = "NAVIGATING"
    _nav_override.pop(session.id, None)
    _last_tick[session.id] = dt.datetime.utcnow()
    _log(db, session.id, "navigation_started", {"target_id": target.id, "destination": {"x": detection.field_x, "y": detection.field_y}})
    db.commit()
    db.refresh(session)
    return session


def return_to_start(db: Session, session: RoverSession) -> RoverSession:
    field = session.field
    start_pos = (field.configuration or {}).get("rover_start", {"x": 0.0, "y": 0.0})
    session.current_target_id = None
    session.status = "NAVIGATING"
    _nav_override[session.id] = (float(start_pos.get("x", 0.0)), float(start_pos.get("y", 0.0)), "return_to_start")
    _last_tick[session.id] = dt.datetime.utcnow()
    _log(db, session.id, "return_to_start_started", {"destination": start_pos})
    db.commit()
    db.refresh(session)
    return session


def pause(db: Session, session: RoverSession) -> RoverSession:
    if session.status == "NAVIGATING":
        _advance(db, session)
        session.status = "PAUSED"
        _log(db, session.id, "paused", {})
        db.commit()
        db.refresh(session)
    return session


def resume(db: Session, session: RoverSession) -> RoverSession:
    if session.status == "PAUSED":
        session.status = "NAVIGATING"
        _last_tick[session.id] = dt.datetime.utcnow()
        _log(db, session.id, "resumed", {})
        db.commit()
        db.refresh(session)
    return session


def stop(db: Session, session: RoverSession) -> RoverSession:
    session.status = "STOPPED"
    session.speed_mps = 0.0
    session.current_target_id = None
    _nav_override.pop(session.id, None)
    _log(db, session.id, "stopped", {})
    db.commit()
    db.refresh(session)
    return session


def emergency_stop(db: Session, session: RoverSession) -> RoverSession:
    session.safety_state = "ESTOP"
    session.status = "SAFETY_LOCK"
    session.speed_mps = 0.0
    _nav_override.pop(session.id, None)
    _log(db, session.id, "emergency_stop", {"triggered_at": dt.datetime.utcnow().isoformat()})
    db.commit()
    db.refresh(session)
    return session


def reset(db: Session, session: RoverSession) -> RoverSession:
    session.safety_state = "NORMAL"
    session.status = "READY"
    session.current_target_id = None
    session.speed_mps = 0.0
    _last_tick[session.id] = dt.datetime.utcnow()
    _log(db, session.id, "reset", {})
    db.commit()
    db.refresh(session)
    return session


def _advance(db: Session, session: RoverSession) -> None:
    """Move the rover toward its current destination based on elapsed time."""
    if session.status != "NAVIGATING" or session.safety_state == "ESTOP":
        return

    now = dt.datetime.utcnow()
    last = _last_tick.get(session.id, now)
    dt_seconds = min(MAX_TICK_SECONDS, max(0.0, (now - last).total_seconds()))
    _last_tick[session.id] = now
    if dt_seconds <= 0:
        return

    dest = _nav_override.get(session.id)
    is_return = dest is not None
    if dest is None:
        target = db.query(Target).filter(Target.id == session.current_target_id).first()
        if target is None or target.detection.field_x is None:
            return
        dest = (target.detection.field_x, target.detection.field_y, target.id)

    dx = dest[0] - session.position_x
    dy = dest[1] - session.position_y
    distance = math.hypot(dx, dy)

    if distance <= ARRIVAL_TOLERANCE_M:
        session.speed_mps = 0.0
        if is_return:
            session.status = "READY"
            _log(db, session.id, "returned_to_start", {})
        else:
            session.status = "INTERVENTION_PENDING"
            _log(db, session.id, "arrived", {"target_id": session.current_target_id})
            _log(db, session.id, "intervention_pending", {"target_id": session.current_target_id})
        _nav_override.pop(session.id, None)
        return

    field = session.field
    obstacles = (field.configuration or {}).get("obstacles", [])
    step = min(distance, DEFAULT_SPEED_MPS * dt_seconds)
    heading = math.degrees(math.atan2(dy, dx))
    next_x = session.position_x + math.cos(math.radians(heading)) * step
    next_y = session.position_y + math.sin(math.radians(heading)) * step

    if in_any_zone(next_x, next_y, obstacles):
        session.status = "ERROR"
        session.speed_mps = 0.0
        _log(db, session.id, "navigation_blocked", {"reason": "obstacle_in_path"})
        return

    session.position_x = round(next_x, 4)
    session.position_y = round(next_y, 4)
    session.heading_deg = round(heading, 2)
    session.speed_mps = DEFAULT_SPEED_MPS


def sync(db: Session, session: RoverSession) -> RoverSession:
    """Advance the simulation and persist. Call before reading status."""
    _advance(db, session)
    db.commit()
    db.refresh(session)
    return session
