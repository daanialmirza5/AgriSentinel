# ml/

Training/validation/export scripts for a real weed/crop YOLO model. These
are **not run as part of this build** — there is no labeled agricultural
dataset in this repository and no training was performed. They are provided
so a real model can be produced later; see `docs/DATASET_GUIDE.md` for
dataset acquisition and annotation guidance first.

## Scripts

- `train.py` — thin, configurable wrapper around `ultralytics.YOLO(...).train(...)`.
- `validate.py` — runs `model.val()` on a held-out split and prints
  precision/recall/mAP50/mAP50-95 (Ultralytics-computed, not invented).
- `export.py` — exports a trained `.pt` checkpoint to ONNX for
  faster/portable CPU inference.

## Example usage (once you have a YOLO-format dataset)

```bash
cd ml
../.venv/Scripts/python train.py --data path/to/data.yaml --model yolov8n.pt --epochs 100 --imgsz 640 --batch 16 --out runs/weed_crop
../.venv/Scripts/python validate.py --weights runs/weed_crop/weights/best.pt --data path/to/data.yaml
../.venv/Scripts/python export.py --weights runs/weed_crop/weights/best.pt --format onnx
```

After training, copy `best.pt` to `models/weed_crop_model.pt` (see
`models/README.md`) and restart the backend, or `POST /api/model/reload`.

## Do not claim results you have not produced

Precision, recall, mAP, confusion matrices, and latency numbers are only
meaningful once `validate.py` has actually been run against a real
held-out split of a real dataset. Nothing in this repository invents those
numbers.
