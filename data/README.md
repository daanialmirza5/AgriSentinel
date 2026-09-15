# data/

Runtime data directory (created automatically, not meant to be hand-edited).

- `uploads/` — original images/videos submitted through the Vision Lab, live
  camera captures, and video processing.
- `results/` — annotated output images produced by the inference service.
- `sample/` — a **synthetic, procedurally generated** demo field image
  (`synthetic_demo_field.jpg`, produced by `scripts/generate_sample_field_image.py`).
  It is not a real farm photograph; it exists only so the Vision Lab can be
  demonstrated without requiring the user to supply their own image. Any
  inspection created from it is a normal inspection record like any other —
  nothing about its detections is fabricated, but the *input* image itself
  is synthetic and is labeled as such directly in the image.
- `agrisentinel.db` — local SQLite database (fields, inspections, detections,
  targets, rover sessions/events, interventions, settings).

To reset all application data, stop the backend and delete this directory's
contents (or just `agrisentinel.db` to keep uploaded files); it will be
recreated automatically on next startup.
