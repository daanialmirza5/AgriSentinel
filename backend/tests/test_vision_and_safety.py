import numpy as np
import pytest

from app.services.localization import pixel_to_field
from app.services.preprocessing import (
    ImageValidationError,
    assess_quality,
    detect_vegetation_blobs,
    load_image_bytes,
    resize_max_dim,
)
from app.services.safety import evaluate_target_safety, in_any_zone


def test_load_image_bytes_rejects_garbage():
    with pytest.raises(ImageValidationError):
        load_image_bytes(b"not an image at all")


def test_resize_max_dim_shrinks_large_image():
    img = np.zeros((2000, 3000, 3), dtype=np.uint8)
    out = resize_max_dim(img, max_dim=1000)
    assert max(out.shape[:2]) <= 1000


def test_assess_quality_flags_blurry_flat_image():
    img = np.full((100, 100, 3), 128, dtype=np.uint8)
    report = assess_quality(img)
    assert report.is_blurry is True


def test_detect_vegetation_blobs_finds_green_region():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:, :] = (40, 60, 90)  # soil-like BGR
    import cv2

    cv2.circle(img, (50, 50), 20, (30, 160, 90), -1)  # green blob
    blobs = detect_vegetation_blobs(img, min_area=50)
    assert len(blobs) >= 1


def test_pixel_to_field_scales_correctly():
    result = pixel_to_field(centroid_x=50, centroid_y=25, image_width=100, image_height=50, field_width_m=20, field_length_m=10)
    assert result.field_x == pytest.approx(10.0)
    assert result.field_y == pytest.approx(5.0)
    assert result.localization_confidence == "approximate"


def test_pixel_to_field_handles_zero_dimensions():
    result = pixel_to_field(0, 0, image_width=0, image_height=0, field_width_m=10, field_length_m=10)
    assert result.localization_confidence == "unavailable"


def test_safety_check_passes_when_all_clear():
    result = evaluate_target_safety(
        confidence=0.8, localization_confidence="approximate", in_restricted_zone=False,
        in_crop_protection_zone=False, rover_speed_mps=0.5, emergency_stop_active=False,
        operator_approved=True,
    )
    assert result.passed is True
    assert result.reasons == []


def test_safety_check_fails_on_estop():
    result = evaluate_target_safety(
        confidence=0.9, localization_confidence="approximate", in_restricted_zone=False,
        in_crop_protection_zone=False, rover_speed_mps=0.0, emergency_stop_active=True,
        operator_approved=True,
    )
    assert result.passed is False
    assert "emergency_stop_clear" in result.reasons


def test_in_any_zone():
    zones = [{"x1": 0, "y1": 0, "x2": 5, "y2": 5}]
    assert in_any_zone(2, 2, zones) is True
    assert in_any_zone(10, 10, zones) is False
