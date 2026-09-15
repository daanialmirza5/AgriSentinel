"""Transparent target priority scoring.

The score and the natural-language explanation are derived from the same
inputs, so the UI can always show *why* a target has the priority it has.
This is a heuristic planning aid, not a yield/economic-damage predictor.
"""
from __future__ import annotations

import math

WEIGHTS = {
    "confidence": 0.5,
    "target_type": 0.3,
    "distance": 0.2,
}

TYPE_WEIGHT = {
    "weed": 1.0,
    "unclassified_vegetation": 0.6,
    "generic_object": 0.2,
    "crop": 0.1,
    "unclassified": 0.3,
}


def score_target(
    *,
    confidence: float,
    target_type: str,
    field_x: float | None,
    field_y: float | None,
    rover_x: float = 0.0,
    rover_y: float = 0.0,
    field_diag_m: float = 1.0,
) -> tuple[float, str]:
    type_component = TYPE_WEIGHT.get(target_type, 0.3)

    if field_x is None or field_y is None:
        distance_component = 0.5
        distance_note = "location unavailable (assumed mid-priority)"
    else:
        dist = math.hypot(field_x - rover_x, field_y - rover_y)
        norm = max(0.001, field_diag_m)
        distance_component = max(0.0, 1.0 - min(1.0, dist / norm))
        distance_note = f"{dist:.2f} m from rover"

    score = (
        WEIGHTS["confidence"] * confidence
        + WEIGHTS["target_type"] * type_component
        + WEIGHTS["distance"] * distance_component
    )
    score = round(min(1.0, max(0.0, score)), 4)

    explanation = (
        f"confidence={confidence:.2f} (weight {WEIGHTS['confidence']}), "
        f"type='{target_type}' factor={type_component:.2f} (weight {WEIGHTS['target_type']}), "
        f"proximity factor={distance_component:.2f} [{distance_note}] (weight {WEIGHTS['distance']}) "
        f"=> score={score:.3f}"
    )
    return score, explanation
