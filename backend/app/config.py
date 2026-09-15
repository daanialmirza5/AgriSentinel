"""Application configuration.

All values can be overridden with environment variables (see .env.example
at the repository root). Nothing here is a secret.
"""
from __future__ import annotations

import os
from pathlib import Path

# Repository root = two levels up from this file (backend/app/config.py -> backend -> root)
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("AGRISENTINEL_DATA_DIR", REPO_ROOT / "data")).resolve()
UPLOADS_DIR = DATA_DIR / "uploads"
RESULTS_DIR = DATA_DIR / "results"
SAMPLE_DIR = DATA_DIR / "sample"
MODELS_DIR = Path(os.environ.get("AGRISENTINEL_MODELS_DIR", REPO_ROOT / "models")).resolve()
DB_PATH = DATA_DIR / "agrisentinel.db"

for d in (UPLOADS_DIR, RESULTS_DIR, SAMPLE_DIR, MODELS_DIR):
    d.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.environ.get("AGRISENTINEL_DATABASE_URL", f"sqlite:///{DB_PATH.as_posix()}")

# --- Model configuration -----------------------------------------------------
# Path to a user-supplied, trained agricultural weed/crop detection model
# (YOLO .pt / .onnx). If it does not exist, the app runs in a clearly labeled
# "model unavailable" state for real inference, and a classical OpenCV
# vegetation-heuristic fallback remains available (also clearly labeled).
CUSTOM_MODEL_PATH = Path(os.environ.get("AGRISENTINEL_MODEL_PATH", MODELS_DIR / "weed_crop_model.pt"))

# Optional: allow downloading a small generic (COCO-pretrained) YOLO model so the
# real inference *pipeline* (loading, running, drawing boxes) can be demonstrated
# end-to-end even without a trained agricultural model. This model is NEVER
# presented as a weed/crop detector -- it is labeled "generic object detector"
# everywhere in the UI and API.
ALLOW_GENERIC_DEMO_MODEL = os.environ.get("AGRISENTINEL_ALLOW_GENERIC_MODEL", "true").lower() == "true"
GENERIC_DEMO_MODEL_FILENAME = "yolov8n.pt"
GENERIC_DEMO_MODEL_PATH = MODELS_DIR / GENERIC_DEMO_MODEL_FILENAME

DEFAULT_CONFIDENCE_THRESHOLD = float(os.environ.get("AGRISENTINEL_CONF_THRESHOLD", "0.35"))

CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB
ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png"}
ALLOWED_VIDEO_EXT = {".mp4", ".avi", ".mov", ".mkv"}

# Video processing: sample at most this many frames per uploaded video to keep
# processing time bounded on CPU-only hardware.
MAX_VIDEO_SAMPLE_FRAMES = 24
