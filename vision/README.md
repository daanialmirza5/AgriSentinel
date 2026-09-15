# vision/

The computer-vision pipeline's actual implementation lives in
`backend/app/services/` (`inference.py`, `preprocessing.py`,
`localization.py`) so it shares code paths with the API rather than
duplicating logic. This directory documents that pipeline and provides a
standalone script for testing camera capture independent of the web server.

## Pipeline stages

1. **Load & validate** (`preprocessing.load_image_bytes`) — decode and
   sanity-check uploaded bytes.
2. **Preprocess** (`preprocessing.resize_max_dim`, `apply_clahe`, `denoise`,
   `assess_quality`) — bound processing cost and improve robustness; each
   step is independently callable and off by default except resizing.
3. **Detect** (`inference.InferenceService.infer`) — YOLO (custom or generic
   demo model) or the classical vegetation heuristic, whichever is active.
4. **Annotate** — bounding boxes drawn back onto the frame with a banner
   indicating whether the mode is a real custom model or a demo/heuristic.
5. **Localize** (`localization.pixel_to_field`) — pixel centroid to
   approximate field coordinates (see `docs/CALIBRATION.md`).

## Standalone camera test

```bash
cd backend
../.venv/Scripts/python -c "import cv2; cap = cv2.VideoCapture(0); ok, frame = cap.read(); print('camera ok:', ok); cap.release()"
```

If `ok` is `False`, no webcam is available on this machine — Live
Monitoring will report the same and the rest of the app remains usable via
image/video upload.
