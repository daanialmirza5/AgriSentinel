# Calibration & Localization

## What is implemented: Option B — controlled simulation mapping

`backend/app/services/localization.py::pixel_to_field()` maps a detection's
pixel centroid to field coordinates by linear scaling:

```
field_x = (pixel_x / image_width)  * field.width_m
field_y = (pixel_y / image_height) * field.length_m
```

This assumes the input image represents a top-down view of the *entire*
configured field extent. It is **not** a camera calibration or homography —
there is no lens-distortion correction, no camera height/angle/pose model,
and no perspective correction. Every localization result is tagged
`localization_confidence: "approximate"` (or `"unavailable"` if image
dimensions are invalid) and `localization_method: "simulated_ground_plane"`
so the UI can always show the caveat rather than implying precision that
doesn't exist.

## Why not full camera calibration (Option A) in this build

A real ground-plane homography needs: a calibrated camera (intrinsics from
a checkerboard capture), a known camera height/tilt relative to the ground
plane, and ideally 4+ known reference points in the scene to solve
`cv2.getPerspectiveTransform` / `cv2.findHomography`. None of this hardware
setup exists in this sprint. `preprocessing.perspective_transform()` is
implemented and unit-testable, ready to be wired up once you have:

1. A fixed, known camera mounting height and downward tilt angle.
2. Four reference points visible in-frame with known real-world
   coordinates (e.g. marked stakes at known field positions).

## Reference-marker mapping (Option C) — extension path

If you place physical markers (e.g. ArUco tags or painted targets) at known
field coordinates, you can:

1. Detect marker pixel positions with `cv2.aruco` (not included in this
   build's dependencies — install `opencv-contrib-python` for it).
2. Solve a homography from marker pixel positions to their known field
   coordinates with `cv2.findHomography`.
3. Replace the linear scaling in `pixel_to_field()` with
   `cv2.perspectiveTransform` using that homography, and change
   `localization_method` to `"reference_marker_homography"`.

## Calibration interface in this build

The Settings page exposes field width/length (used directly by the Option B
mapping) but does not yet expose a dedicated calibration panel (reference
points, camera height/angle inputs, mapping preview). That panel is a
natural next addition once Option A or C is implemented — building it
against the current Option B mapping would create a false impression of
precision, so it was deliberately left out rather than added as a
non-functional placeholder.

## Validating localization once you calibrate

Do not report centimeter-level accuracy without measuring it. A simple
validation: place objects at known field coordinates, run detection, and
compare `detection.field_x/field_y` against ground truth; record the error
distribution before making any accuracy claim.
