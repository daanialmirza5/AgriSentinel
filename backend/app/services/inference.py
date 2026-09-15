"""Detection inference service.

Two detection backends are supported and are always clearly labeled:

1. YOLO backend (Ultralytics). Loaded from:
   - a user-supplied, trained agricultural model at
     ``AGRISENTINEL_MODEL_PATH`` (labeled as a real weed/crop model), or
   - a small pretrained COCO checkpoint (yolov8n.pt) used ONLY to demonstrate
     the real inference pipeline end-to-end. This is ALWAYS labeled
     "generic object detector - not trained for weeds/crops" and its
     detections are never reported as weed/crop classifications.

2. Classical vegetation-heuristic backend (pure OpenCV, see preprocessing.py).
   Used when no YOLO backend is available, or selected explicitly. Clearly
   labeled as a non-ML color-segmentation heuristic.

If neither is usable the service reports MODEL_UNAVAILABLE and the API
returns an explicit "model unavailable" response rather than inventing
detections.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np

from app.config import ALLOW_GENERIC_DEMO_MODEL, CUSTOM_MODEL_PATH, GENERIC_DEMO_MODEL_FILENAME, GENERIC_DEMO_MODEL_PATH
from app.services.preprocessing import detect_vegetation_blobs

COCO_TO_TARGET_TYPE = "generic_object"


@dataclass
class DetectionResult:
    class_id: int
    class_name: str
    target_type: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float
    centroid_x: float
    centroid_y: float


@dataclass
class ModelStatus:
    backend: str = "none"  # yolo|classical|none
    installed: bool = False
    loaded: bool = False
    is_generic_demo: bool = False
    model_path: str = ""
    model_filename: str = ""
    model_format: str = ""
    task: str = ""
    version: str = ""
    device: str = "cpu"
    error: Optional[str] = None
    label: str = "Model unavailable"
    warning: Optional[str] = None


def _classify_target_type(class_name: str) -> str:
    name = class_name.lower()
    if "weed" in name:
        return "weed"
    if "crop" in name:
        return "crop"
    return "unclassified"


class InferenceService:
    def __init__(self) -> None:
        self.status = ModelStatus()
        self._model = None
        self._ultralytics_available = False
        self._load()

    # -- loading ------------------------------------------------------
    def _load(self) -> None:
        try:
            from ultralytics import YOLO  # noqa: F401
            self._ultralytics_available = True
        except Exception as exc:  # pragma: no cover - environment dependent
            self.status = ModelStatus(
                backend="classical",
                installed=False,
                loaded=False,
                error=f"ultralytics not importable: {exc}",
                label="Classical vegetation heuristic (YOLO engine unavailable)",
            )
            return

        from ultralytics import YOLO

        if CUSTOM_MODEL_PATH.exists():
            try:
                model = YOLO(str(CUSTOM_MODEL_PATH))
                self._model = model
                self.status = ModelStatus(
                    backend="yolo",
                    installed=True,
                    loaded=True,
                    is_generic_demo=False,
                    model_path=str(CUSTOM_MODEL_PATH),
                    model_filename=CUSTOM_MODEL_PATH.name,
                    model_format=CUSTOM_MODEL_PATH.suffix.lstrip("."),
                    task=getattr(model, "task", "detect") or "detect",
                    version="user-supplied",
                    label=f"Custom agricultural model ({CUSTOM_MODEL_PATH.name})",
                )
                return
            except Exception as exc:
                self.status = ModelStatus(
                    backend="classical",
                    installed=True,
                    loaded=False,
                    error=f"Failed to load custom model: {exc}",
                    label="Classical vegetation heuristic (custom model failed to load)",
                )
                return

        if ALLOW_GENERIC_DEMO_MODEL:
            try:
                if GENERIC_DEMO_MODEL_PATH.exists():
                    model = YOLO(str(GENERIC_DEMO_MODEL_PATH))
                else:
                    model = YOLO(GENERIC_DEMO_MODEL_FILENAME)  # auto-downloads to CWD
                    downloaded = Path(GENERIC_DEMO_MODEL_FILENAME)
                    if downloaded.exists():
                        downloaded.replace(GENERIC_DEMO_MODEL_PATH)
                self._model = model
                self.status = ModelStatus(
                    backend="yolo",
                    installed=True,
                    loaded=True,
                    is_generic_demo=True,
                    model_path=str(GENERIC_DEMO_MODEL_PATH),
                    model_filename=GENERIC_DEMO_MODEL_FILENAME,
                    model_format="pt",
                    task=getattr(model, "task", "detect") or "detect",
                    version="pretrained-coco",
                    label="Generic object detector (COCO-pretrained YOLOv8n) - NOT a weed/crop model",
                    warning=(
                        "No trained agricultural model is installed. Running a generic "
                        "pretrained detector for pipeline demonstration only; its class "
                        "labels are ordinary objects, not weeds or crops. Install a real "
                        "model per docs/DATASET_GUIDE.md for genuine weed/crop detection."
                    ),
                )
                return
            except Exception as exc:
                self.status = ModelStatus(
                    backend="classical",
                    installed=False,
                    loaded=False,
                    error=f"Could not fetch generic demo model (offline?): {exc}",
                    label="Classical vegetation heuristic (no YOLO model available)",
                )
                return

        self.status = ModelStatus(
            backend="classical",
            installed=False,
            loaded=False,
            label="Classical vegetation heuristic (no YOLO model configured)",
        )

    def reload(self) -> None:
        self._model = None
        self._load()

    # -- inference ------------------------------------------------------
    def infer(
        self, img: np.ndarray, conf_threshold: float = 0.35, force_classical: bool = False
    ) -> tuple[list[DetectionResult], np.ndarray, dict[str, Any]]:
        """Run detection on a BGR image. Returns (detections, annotated_bgr, meta)."""
        start = time.perf_counter()
        if self.status.backend == "yolo" and self._model is not None and not force_classical:
            detections = self._infer_yolo(img, conf_threshold)
            mode = "yolo_generic_demo" if self.status.is_generic_demo else "yolo_custom_model"
        else:
            detections = self._infer_classical(img)
            mode = "classical_vegetation_heuristic"
        elapsed_ms = (time.perf_counter() - start) * 1000
        annotated = self._annotate(img, detections, mode)
        meta = {
            "detection_mode": mode,
            "processing_time_ms": elapsed_ms,
            "model_name": self.status.model_filename or "classical-cv",
            "model_version": self.status.version or "n/a",
        }
        return detections, annotated, meta

    def _infer_yolo(self, img: np.ndarray, conf_threshold: float) -> list[DetectionResult]:
        assert self._model is not None
        results = self._model.predict(img, conf=conf_threshold, verbose=False)
        detections: list[DetectionResult] = []
        if not results:
            return detections
        r = results[0]
        names = r.names
        if r.boxes is None:
            return detections
        for box in r.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
            class_name = names.get(cls_id, str(cls_id)) if isinstance(names, dict) else str(names[cls_id])
            target_type = COCO_TO_TARGET_TYPE if self.status.is_generic_demo else _classify_target_type(class_name)
            detections.append(
                DetectionResult(
                    class_id=cls_id,
                    class_name=class_name,
                    target_type=target_type,
                    confidence=conf,
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                    centroid_x=(x1 + x2) / 2,
                    centroid_y=(y1 + y2) / 2,
                )
            )
        return detections

    def _infer_classical(self, img: np.ndarray) -> list[DetectionResult]:
        blobs = detect_vegetation_blobs(img)
        detections = []
        for b in blobs[:40]:
            detections.append(
                DetectionResult(
                    class_id=-1,
                    class_name="vegetation_region",
                    target_type="unclassified_vegetation",
                    confidence=round(min(0.99, b.greenness), 3),
                    x1=float(b.x1),
                    y1=float(b.y1),
                    x2=float(b.x2),
                    y2=float(b.y2),
                    centroid_x=float((b.x1 + b.x2) / 2),
                    centroid_y=float((b.y1 + b.y2) / 2),
                )
            )
        return detections

    def _annotate(self, img: np.ndarray, detections: list[DetectionResult], mode: str) -> np.ndarray:
        out = img.copy()
        color_map = {
            "weed": (0, 0, 255),
            "crop": (0, 200, 0),
            "unclassified_vegetation": (0, 200, 255),
            "generic_object": (255, 150, 0),
            "unclassified": (200, 200, 200),
        }
        for d in detections:
            color = color_map.get(d.target_type, (200, 200, 200))
            p1, p2 = (int(d.x1), int(d.y1)), (int(d.x2), int(d.y2))
            cv2.rectangle(out, p1, p2, color, 2)
            label = f"{d.class_name} {d.confidence:.2f}"
            cv2.putText(out, label, (p1[0], max(0, p1[1] - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
        banner = "SIMULATED/DEMO DETECTION MODE" if mode != "yolo_custom_model" else "MODEL: CUSTOM AGRICULTURAL"
        cv2.putText(out, banner, (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
        return out


inference_service = InferenceService()
