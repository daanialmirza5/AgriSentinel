"""Generate a synthetic demo field image for the Vision Lab "load sample" button.

This is NOT a real farm photograph. It is a procedurally generated image with
soil-colored background, straight crop rows, and scattered irregular green
blobs standing in for weeds, used only so the demo can be exercised without
requiring the user to supply their own image. The API and UI label any
inspection created from it as based on a synthetic sample image.
"""
from __future__ import annotations

import random
from pathlib import Path

import cv2
import numpy as np

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "sample"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def make_field_image(width=960, height=640, seed=42) -> np.ndarray:
    rng = random.Random(seed)
    img = np.zeros((height, width, 3), dtype=np.uint8)
    soil_base = np.array([35, 65, 95], dtype=np.uint8)  # BGR brown
    noise = (np.random.default_rng(seed).normal(0, 8, (height, width, 3))).astype(np.int16)
    img[:, :] = soil_base
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    row_spacing = width // 8
    row_width = 26
    crop_green = (40, 140, 40)  # BGR - crop rows, slightly different shade than weeds
    for rx in range(row_spacing // 2, width, row_spacing):
        cv2.rectangle(img, (rx - row_width // 2, 0), (rx + row_width // 2, height), crop_green, -1)
        for cy in range(20, height, 34):
            cv2.ellipse(img, (rx, cy), (row_width, 14), 0, 0, 360, (55, 170, 55), -1)

    weed_green = (30, 100, 190)  # BGR-ish, will look distinct after HSV thresholding too but visually different shape
    weed_positions = [(rng.randint(40, width - 40), rng.randint(40, height - 40)) for _ in range(14)]
    for (wx, wy) in weed_positions:
        r = rng.randint(10, 22)
        pts = []
        for a in range(0, 360, 30):
            rad = r + rng.randint(-4, 4)
            x = int(wx + rad * np.cos(np.radians(a)))
            y = int(wy + rad * np.sin(np.radians(a)))
            pts.append([x, y])
        cv2.fillPoly(img, [np.array(pts, dtype=np.int32)], (25, 160, 90))

    cv2.putText(img, "SYNTHETIC DEMO IMAGE - NOT A REAL FIELD PHOTO", (10, height - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    return img


if __name__ == "__main__":
    img = make_field_image()
    out_path = OUT_DIR / "synthetic_demo_field.jpg"
    cv2.imwrite(str(out_path), img)
    print(f"Wrote {out_path}")
