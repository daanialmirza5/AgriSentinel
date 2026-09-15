"""Target localization: pixel coordinates -> approximate field coordinates.

MVP implementation uses **Option B - controlled simulation mapping** from
PART 8.2 of the product spec: a documented linear mapping from image pixel
space to the configured field's physical dimensions. It assumes the uploaded
image represents a top-down (or simulated top-down) view of the full field
extent. This is NOT a calibrated camera/homography solution and every result
carries an explicit "approximate" localization_confidence plus the method
name so the UI can show the appropriate warning. See docs/CALIBRATION.md.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LocalizationResult:
    field_x: float
    field_y: float
    localization_confidence: str  # "approximate" | "unavailable"
    method: str


def pixel_to_field(
    centroid_x: float,
    centroid_y: float,
    image_width: int,
    image_height: int,
    field_width_m: float,
    field_length_m: float,
) -> LocalizationResult:
    if image_width <= 0 or image_height <= 0:
        return LocalizationResult(0.0, 0.0, "unavailable", "simulated_ground_plane")

    fx = (centroid_x / image_width) * field_width_m
    fy = (centroid_y / image_height) * field_length_m
    return LocalizationResult(
        field_x=round(fx, 3),
        field_y=round(fy, 3),
        localization_confidence="approximate",
        method="simulated_ground_plane",
    )
