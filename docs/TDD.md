# AgriSentinel — Technical Design Document

Describes what was actually built, not an aspirational architecture.

## 1. Architecture

```
frontend/ (React + TypeScript + Vite)  --proxy-->  backend/ (FastAPI + SQLAlchemy + SQLite)
                                                          |
                                                          +-- app/services/inference.py   (YOLO or classical CV)
                                                          +-- app/services/preprocessing.py (OpenCV)
                                                          +-- app/services/localization.py (pixel -> field coords)
                                                          +-- app/services/rover_simulator.py (2D sim, pull-based)
                                                          +-- app/services/safety.py       (shared safety gate)
                                                          +-- app/services/actuator.py     (simulated + hardware stub)
                                                          +-- app/services/analytics.py / reports.py
                                                          +-- data/agrisentinel.db (SQLite)
                                                          +-- data/uploads, data/results (static-served under /media)
```

The frontend is a single Vite dev server; in production it would be built
(`npm run build`) and served as static files (see `docs/DEPLOYMENT.md`). The
backend is a single FastAPI process; there is no message queue, no
background worker, and no separate microservices — deliberately, given the
scope and time budget.

## 2. Data flow (image inspection -> target -> rover -> intervention)

1. `POST /api/inspect/image?field_id=...` (multipart file) decodes the
   image (`preprocessing.load_image_bytes`), resizes it
   (`resize_max_dim`), and calls `InferenceService.infer()`.
2. `InferenceService` picks a backend: a loaded YOLO model (custom or
   generic-demo) or the classical vegetation heuristic, per
   `settings.detection_backend_preference` (`auto` prefers YOLO).
3. Detections are persisted as `Detection` rows; each is passed through
   `localization.pixel_to_field()` to get an approximate field coordinate,
   and through `target_planner.score_target()` to get a transparent
   priority score. A `Target` row is created per detection.
4. The frontend polls `/api/targets` and lets an operator approve/plan a
   target, then calls `/api/rover/navigate` with a `target_id`.
5. `rover_simulator.navigate_to_target()` checks the destination isn't in a
   restricted zone, then flips the `RoverSession` to `NAVIGATING`.
6. Every subsequent `GET /api/rover/status` calls `rover_simulator.sync()`,
   which advances the rover's position based on real elapsed time
   (`_advance()`), persists it, and logs `RoverEvent` rows for major
   transitions (arrival, blocking, etc.).
7. On arrival the rover moves to `INTERVENTION_PENDING`. `POST
   /api/actuator/simulate` re-runs the full safety gate
   (`safety.evaluate_target_safety`) and, if it passes, executes
   `SimulatedActuator.execute()`, records an `Intervention` row, and marks
   the `Target`/`RoverSession` `COMPLETED`.
8. Analytics (`GET /api/analytics/summary`) and CSV reports
   (`GET /api/reports/*.csv`) are computed directly from these tables on
   every request — nothing is cached or precomputed, and nothing is
   fabricated when tables are empty (explicit `None`/`0` values, not
   invented numbers).

## 3. Database

SQLite via SQLAlchemy 2.0 declarative models
(`backend/app/models/*.py`). Schema is created with
`Base.metadata.create_all()` on startup (`init_db()`), documented as the
initialization procedure — there is no Alembic migration chain in this
build. Tables: `fields`, `monitoring_sessions`, `inspections`,
`detections`, `targets`, `rover_sessions`, `rover_events`,
`interventions`, `settings`. Foreign keys and indexes are declared per
`backend/app/models/*.py`; cascading deletes are used so deleting a field
or inspection cleans up its dependents.

## 4. Inference backends and honesty guarantees

See `backend/app/services/inference.py` docstring. Summary: a detection's
`class_name`/`target_type` always reflects what actually produced it —
`weed`/`crop` only for a real custom model whose class names say so,
`generic_object` for the COCO demo model, `unclassified_vegetation` for the
classical heuristic. The `detection_mode` field on every `Inspection` row
records exactly which path ran. `GET /api/model/status` always reflects the
actual loaded state, including a `warning` string when running in
generic-demo mode.

## 5. Rover simulation

See `robotics/README.md`. Key point: simulation state (`RoverSession`) is
the source of truth in the database; a small in-memory dict
(`_last_tick`, `_nav_override` in `rover_simulator.py`) tracks
wall-clock deltas between polls and any "return to start" pseudo-target.
This means a backend restart resets in-flight navigation timing but not
persisted position/status — acceptable for a simulation, called out here
rather than hidden.

## 6. Safety

A single function, `safety.evaluate_target_safety()`, is the only place
that decides whether an action may proceed. It is called by
`/api/actuator/simulate` before any actuation. `/api/rover/navigate`
separately refuses to start navigation into a restricted zone and refuses
any command while `safety_state == "ESTOP"`. Emergency stop
(`/api/rover/emergency-stop`) is unconditional — it does not check any
other state — and requires an explicit `/api/rover/reset` before further
motion or actuation.

## 7. Frontend

React 18 + TypeScript, `react-router-dom` for the 9 pages, a small
`FieldContext` for the globally-selected field (persisted to
`localStorage`), a hand-written CSS design system (no Tailwind/UI kit
dependency) in `src/index.css`, and Recharts for the two chart types on
the Analytics page. State is fetched directly from the API per page (no
global cache/store) with `setInterval` polling (1-2s) on pages that show
live rover/camera state — there is no WebSocket layer in this build.

## 8. Known tradeoffs / not built

- No Alembic migrations (create_all only).
- No WebSocket push; live pages poll.
- No multi-rover support (one active `RoverSession` per field at a time).
- No real camera calibration (see `docs/CALIBRATION.md` — Option B,
  simulated ground-plane mapping, is implemented; Options A/C are not).
- Video processing samples up to `MAX_VIDEO_SAMPLE_FRAMES` (24) frames
  rather than every frame, to keep CPU processing time bounded.
- No trained agricultural model ships with this build (no dataset was
  available/trained in this sprint) — see `docs/DATASET_GUIDE.md`.
- Frontend has no automated test suite in this build (see
  `docs/TESTING.md`); it was verified manually via a scripted Playwright
  smoke pass during development.
