# models/

This directory holds detection model weights. Nothing here is committed to
version control except this file (see `.gitignore`).

## Files the app looks for

- `weed_crop_model.pt` (or the path set in `AGRISENTINEL_MODEL_PATH`) — a
  **real, trained** YOLO detection/segmentation checkpoint for weeds/crops.
  If present, AgriSentinel loads it and labels every detection with its
  actual class names.
- `yolov8n.pt` — auto-downloaded on first run (if `AGRISENTINEL_ALLOW_GENERIC_MODEL=true`
  and network access is available) as a **generic, non-agricultural**
  pretrained COCO detector, used only to exercise the real inference
  pipeline end-to-end. It is always labeled "generic object detector — not a
  weed/crop model" in the UI and API and its detections are never reported
  as weeds or crops.

## Installing a real agricultural model

1. Train or otherwise obtain a YOLO-format weed/crop detection model (see
   `docs/DATASET_GUIDE.md` for dataset sources and `ml/train.py` for a
   documented training entry point).
2. Copy the resulting `best.pt` (or exported `.onnx`) here as
   `weed_crop_model.pt`, or point `AGRISENTINEL_MODEL_PATH` at it.
3. Restart the backend, or call `POST /api/model/reload`.
4. Confirm via `GET /api/model/status` that `is_generic_demo` is `false`
   and `label` names your model file.

If no model is installed and network access is unavailable, the app falls
back to the classical OpenCV vegetation-heuristic detector (see
`backend/app/services/preprocessing.py`), which is clearly labeled as a
non-ML heuristic in every response.
