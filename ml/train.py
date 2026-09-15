"""Train a YOLO weed/crop detection model.

Not executed as part of this build (no labeled dataset is present). Requires
`ultralytics` (already in backend/requirements.txt) and a YOLO-format
dataset with a data.yaml (see docs/DATASET_GUIDE.md).

Example:
    python train.py --data path/to/data.yaml --model yolov8n.pt --epochs 100 --imgsz 640 --batch 16
"""
from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Train an AgriSentinel weed/crop YOLO model.")
    parser.add_argument("--data", required=True, help="Path to YOLO data.yaml")
    parser.add_argument("--model", default="yolov8n.pt", help="Base checkpoint to fine-tune from")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--out", default="runs/agrisentinel", help="Output project directory")
    parser.add_argument("--seed", type=int, default=42, help="Reproducibility seed")
    args = parser.parse_args()

    from ultralytics import YOLO

    model = YOLO(args.model)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project=args.out,
        seed=args.seed,
    )
    print(f"Training complete. Weights saved under {args.out}/weights/best.pt")
    print("Copy that file to models/weed_crop_model.pt to use it in AgriSentinel.")


if __name__ == "__main__":
    main()
