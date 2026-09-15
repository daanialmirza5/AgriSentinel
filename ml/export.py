"""Export a trained YOLO checkpoint to a portable inference format.

Not executed as part of this build.

Example:
    python export.py --weights runs/agrisentinel/weights/best.pt --format onnx
"""
from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Export an AgriSentinel weed/crop YOLO model.")
    parser.add_argument("--weights", required=True)
    parser.add_argument("--format", default="onnx", choices=["onnx", "torchscript", "openvino"])
    args = parser.parse_args()

    from ultralytics import YOLO

    model = YOLO(args.weights)
    out_path = model.export(format=args.format)
    print(f"Exported to {out_path}")


if __name__ == "__main__":
    main()
