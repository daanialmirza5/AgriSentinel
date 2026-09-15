"""Reusable OpenCV preprocessing utilities.

These are real, deterministic image-processing operations (no ML). They are
used both to prepare frames before inference and to power the classical
"vegetation heuristic" fallback detector used when no trained YOLO model is
available (see services/inference.py).
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


class ImageValidationError(ValueError):
    pass


def load_image_bytes(data: bytes) -> np.ndarray:
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ImageValidationError("File could not be decoded as an image.")
    return img


def resize_max_dim(img: np.ndarray, max_dim: int = 1280) -> np.ndarray:
    h, w = img.shape[:2]
    scale = min(1.0, max_dim / max(h, w))
    if scale < 1.0:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return img


def to_gray(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def apply_clahe(img: np.ndarray, clip_limit: float = 2.0, tile: int = 8) -> np.ndarray:
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile, tile))
    l2 = clahe.apply(l)
    return cv2.cvtColor(cv2.merge((l2, a, b)), cv2.COLOR_LAB2BGR)


def denoise(img: np.ndarray) -> np.ndarray:
    return cv2.fastNlMeansDenoisingColored(img, None, 5, 5, 7, 21)


def blur_score(img: np.ndarray) -> float:
    """Variance of the Laplacian. Lower means blurrier."""
    gray = to_gray(img)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


@dataclass
class ImageQualityReport:
    width: int
    height: int
    blur_score: float
    is_blurry: bool
    mean_brightness: float


def assess_quality(img: np.ndarray, blur_threshold: float = 60.0) -> ImageQualityReport:
    h, w = img.shape[:2]
    b = blur_score(img)
    brightness = float(to_gray(img).mean())
    return ImageQualityReport(width=w, height=h, blur_score=b, is_blurry=b < blur_threshold, mean_brightness=brightness)


def extract_roi(img: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> np.ndarray:
    h, w = img.shape[:2]
    x1, x2 = sorted((max(0, x1), min(w, x2)))
    y1, y2 = sorted((max(0, y1), min(h, y2)))
    return img[y1:y2, x1:x2]


def perspective_transform(img: np.ndarray, src_pts: np.ndarray, dst_pts: np.ndarray, out_size: tuple[int, int]):
    """Apply a 4-point perspective transform (ground-plane rectification)."""
    m = cv2.getPerspectiveTransform(src_pts.astype(np.float32), dst_pts.astype(np.float32))
    return cv2.warpPerspective(img, m, out_size)


# ---------------------------------------------------------------------------
# Classical vegetation-blob heuristic (NOT machine learning, NOT weed/crop
# classification). Used only as a transparent fallback so the rest of the
# pipeline (localization, targets, rover, safety) can be exercised on real
# uploaded images when no trained agricultural model is installed.
# ---------------------------------------------------------------------------
@dataclass
class VegetationBlob:
    x1: int
    y1: int
    x2: int
    y2: int
    area: int
    greenness: float  # 0..1, relative strength of the vegetation color signal


def detect_vegetation_blobs(img: np.ndarray, min_area: int = 250) -> list[VegetationBlob]:
    """Segment plausible plant/vegetation regions using an HSV green-band
    threshold plus morphological cleanup, then return connected-component
    bounding boxes. This is a classical heuristic, not a trained classifier,
    and cannot distinguish weeds from crops.
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower = np.array([25, 30, 30])
    upper = np.array([95, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    blobs: list[VegetationBlob] = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area:
            continue
        x, y, w, h = cv2.boundingRect(c)
        region_mask = mask[y : y + h, x : x + w] > 0
        greenness = float(region_mask.mean()) if region_mask.size else 0.0
        blobs.append(VegetationBlob(x1=x, y1=y, x2=x + w, y2=y + h, area=int(area), greenness=greenness))
    blobs.sort(key=lambda b: b.area, reverse=True)
    return blobs
