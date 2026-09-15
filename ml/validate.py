"""Validate a trained YOLO weed/crop model and print real metrics.

Not executed as part of this build. Prints whatever Ultralytics actually
computes -- precision, recall, mAP50, mAP50-95, per-class breakdown -- with
no fabricated numbers.

Example:
    python validate.py --weights runs/agrisentinel/weights/best.pt --data path/to/data.yaml
"""
from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate an AgriSentinel weed/crop YOLO model.")
    parser.add_argument("--weights", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--imgsz", type=int, default=640)
    args = parser.parse_args()

    from ultralytics import YOLO

    model = YOLO(args.weights)
    metrics = model.val(data=args.data, imgsz=args.imgsz)
    print("mAP50:", metrics.box.map50)
    print("mAP50-95:", metrics.box.map)
    print("Per-class mAP50-95:", dict(zip(model.names.values(), metrics.box.maps)))


if __name__ == "__main__":
    main()
