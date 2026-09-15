"""Safety gate shared by the actuator and rover services.

Every automated action (simulated spray/marker, or rover navigation to a
target) must pass through here. All checks are real, deterministic, and
logged - none of them are decorative.
"""
from __future__ import annotations

from dataclasses import dataclass, field

MIN_ACTION_CONFIDENCE = 0.30
MAX_SAFE_SPEED_MPS = 2.0


@dataclass
class SafetyCheckResult:
    passed: bool
    checks: dict[str, bool] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)


def evaluate_target_safety(
    *,
    confidence: float,
    localization_confidence: str,
    in_restricted_zone: bool,
    in_crop_protection_zone: bool,
    rover_speed_mps: float,
    emergency_stop_active: bool,
    operator_approved: bool,
    require_operator_approval: bool = True,
) -> SafetyCheckResult:
    checks = {
        "confidence_ok": confidence >= MIN_ACTION_CONFIDENCE,
        "localization_valid": localization_confidence != "unavailable",
        "outside_restricted_zone": not in_restricted_zone,
        "outside_crop_protection_zone": not in_crop_protection_zone,
        "speed_safe": rover_speed_mps <= MAX_SAFE_SPEED_MPS,
        "emergency_stop_clear": not emergency_stop_active,
        "operator_approved": operator_approved or not require_operator_approval,
    }
    reasons = [name for name, ok in checks.items() if not ok]
    return SafetyCheckResult(passed=len(reasons) == 0, checks=checks, reasons=reasons)


def point_in_zone(x: float, y: float, zone: dict) -> bool:
    """Zones are axis-aligned rectangles: {x1,y1,x2,y2} in field-meter coords."""
    return zone["x1"] <= x <= zone["x2"] and zone["y1"] <= y <= zone["y2"]


def in_any_zone(x: float, y: float, zones: list[dict]) -> bool:
    return any(point_in_zone(x, y, z) for z in zones or [])
