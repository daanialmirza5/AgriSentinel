# Dataset Guide

No dataset is bundled with this build and no model was trained. This guide
covers how to get a real weed/crop model working with AgriSentinel.

## Candidate public datasets

### DeepWeeds
- ~17,500 labeled images of 8 weed species from Australian rangelands.
- Originally a **classification** dataset (one label per image), not
  object detection with bounding boxes. To use it for YOLO-style detection
  you would need to either (a) treat it as a classification problem with a
  separate pipeline, or (b) re-annotate a subset with bounding boxes.
- Check the current license and citation terms at the official repository
  before use; do not assume redistribution rights.

### PlantVillage
- Leaf-level crop disease classification images. Useful for a **future**
  crop-health/disease classification extension, but this is a different
  task from field-level weed/crop detection — do not conflate the two.
  A model trained on PlantVillage leaf crops does not detect weeds in a
  field image.

### Custom field imagery (recommended for a real deployment)
Collect your own images because public datasets rarely match your camera
height, crop variety, growth stage, and lighting:
- Vary: crop rows, growth stages, soil types, shadows/sunlight, camera
  height and angle, weather, weed density, occlusion, and visually similar
  crop/weed pairs.
- Capture roughly top-down or oblique-downward, consistent with how the
  rover/camera would actually be mounted.
- Aim for at least a few hundred images per class before a first useful
  model; several thousand for production quality.

## Annotation

- Use a bounding-box annotation tool (e.g. an open-source tool such as
  LabelImg or CVAT) and export in YOLO format (`class x_center y_center
  width height`, normalized 0-1, one `.txt` per image).
- Define classes explicitly, e.g. `0: crop`, `1: weed` (or per-species
  classes if you need that granularity). Keep a `classes.txt` /
  `data.yaml` mapping IDs to names — AgriSentinel's `_classify_target_type()`
  (`backend/app/services/inference.py`) maps any class name containing
  "weed" to `target_type=weed` and "crop" to `target_type=crop"`, so naming
  classes accordingly keeps the app's labeling honest with zero extra code.

## Train / validation / test split

- Split at the **image** level, not the annotation level, so no image (and
  no near-duplicate frame from the same video) appears in more than one
  split — this prevents data leakage that would inflate validation
  metrics.
- A reasonable starting split: 70% train / 20% validation / 10% test.

## Data quality checks

- Verify every image has a matching label file (or is intentionally
  background-only).
- Check class balance; heavily imbalanced classes need either more data or
  class-weighted loss.
- Spot-check a random sample of rendered boxes for annotation correctness.

## Training

See `ml/train.py`, `ml/validate.py`, `ml/export.py` — thin, documented
wrappers around the Ultralytics YOLO API. Example:

```bash
cd ml
../.venv/Scripts/python train.py --data path/to/data.yaml --model yolov8n.pt --epochs 100 --imgsz 640 --batch 16
```

After training, copy `best.pt` to `models/weed_crop_model.pt` and restart
the backend (or `POST /api/model/reload`). `GET /api/model/status` should
then show `is_generic_demo: false` and your model's filename.

## Evaluation

`ml/validate.py` reports Ultralytics' own computed precision, recall,
mAP50, and mAP50-95 (overall and per-class) on your validation/test split —
these are the only performance numbers AgriSentinel will ever report, and
only once you've actually run validation. Localization/targeting error is
not automatically measured in this build; if you calibrate a real camera
(`docs/CALIBRATION.md`), measure it manually against known reference points.
