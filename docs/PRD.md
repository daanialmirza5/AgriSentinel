# AgriSentinel — Product Requirements (as implemented)

**Tagline:** See the field. Find the weeds. Protect the crop.

This document summarizes the product actually delivered in this build. The
full original specification (all 27 parts) drove the design; this is the
as-built subset, kept short deliberately rather than restating the entire
spec.

## Problem

Manual crop scouting is slow and broad chemical treatment is wasteful.
AgriSentinel demonstrates an end-to-end pipeline — image capture, weed/crop
detection, field-coordinate localization, target prioritization, and a
simulated rover + actuator — that a real precision-agriculture system would
need, while being explicit about which parts are real (image processing,
persistence, safety logic) and which are simulated (rover motion,
actuation) or best-effort demo (the bundled COCO-pretrained model).

## Users

- **Farmer** — views field state, uploads imagery, reviews targets/history.
- **Operator** — runs live monitoring, drives the rover simulation, approves
  interventions, uses emergency stop.
- **Researcher** — inspects raw detections/confidence, exports CSVs, extends
  the model via `ml/`.
- **Owner** (you) — configures fields, model path, and thresholds in
  Settings.

## Delivered modules

| Module | Status |
|---|---|
| Dashboard (Overview) | Built — live stats from the database, empty states when no data |
| Vision Lab (image + video upload) | Built — real OpenCV decode + inference, video is frame-sampled |
| Live Monitoring (webcam) | Built — OpenCV `VideoCapture` + MJPEG stream; reports clearly if no camera |
| Detection (YOLO + classical fallback) | Built — see `backend/app/services/inference.py` |
| Target localization | Built — simulated ground-plane mapping (Option B), documented in `CALIBRATION.md` |
| Rover simulator | Built — full state machine, time-based 2D navigation |
| Target planner | Built — transparent, explainable priority score |
| Simulated actuator | Built — harmless virtual marker; hardware interface documented, not implemented |
| Safety system | Built — confidence/zone/speed/e-stop/approval gate on every actuation |
| Field map | Built — 2D SVG map with zones, targets, rover position |
| History & analytics | Built — real DB-derived stats, CSV export |
| Settings | Built — model status, detection backend, thresholds, field CRUD |
| Documentation | Built — this file plus TDD/DATASET_GUIDE/CALIBRATION/HARDWARE_INTEGRATION/TESTING/DEPLOYMENT |

## Explicit non-claims

- No real agricultural weed/crop model ships with this build — see
  `docs/DATASET_GUIDE.md` for how to train and install one.
- The rover and actuator are 100% software simulation. No physical hardware
  is controlled or connected.
- Localization is an approximate simulated mapping, not a calibrated
  camera/homography solution.
- No yield, pesticide-reduction, or economic-impact metrics are computed or
  claimed anywhere in the app.
- No production/commercial/agricultural certification is claimed.

## Out of scope for this build (documented, not built)

- Multi-rover fleets, WebSocket push updates, Alembic migrations, GPS/RTK
  integration, real camera calibration, automated CI pipeline.
