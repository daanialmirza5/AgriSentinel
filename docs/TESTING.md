# Testing

## Backend (implemented, passing)

```bash
cd backend
../.venv/Scripts/python -m pytest tests -v
```

Actual result at time of writing: **31 passed**, 0 failed, ~8s runtime.
Tests use an isolated temp SQLite database per run (see
`backend/tests/conftest.py`) and force the classical vegetation-heuristic
detection backend (`AGRISENTINEL_ALLOW_GENERIC_MODEL=false`) so tests run
fast and offline without depending on a network download.

Coverage:
- `test_health_and_fields.py` — health endpoint, model-status shape, field
  CRUD, input validation (rejects non-positive dimensions).
- `test_inspections.py` — image inspection end-to-end (creates detections +
  targets), rejects bad extensions/corrupt files/missing fields, delete.
- `test_targets.py` — approve/plan/skip lifecycle, status filtering,
  invalid-transition rejection.
- `test_rover_and_actuator.py` — rover start/status, full navigate-to-arrival
  cycle (real time-based polling, not mocked), emergency stop blocking
  navigation and requiring reset, actuator safety-check blocking
  (low confidence, missing operator approval) and success path.
- `test_analytics_settings_reports.py` — empty-state analytics, populated
  analytics, settings round-trip, CSV export content.
- `test_vision_and_safety.py` — image validation, resize, blur/quality
  detection, classical vegetation blob detection, pixel-to-field scaling
  (including the zero-dimension edge case), safety-gate pass/fail logic,
  zone containment.

### Known warnings (non-failing)

`datetime.datetime.utcnow()` deprecation warnings (Python 3.12) and one
SQLAlchemy 2.0 `Query.get()` legacy-API warning appear in test output.
They do not affect correctness and were left as-is to keep the sprint
focused on functional coverage over stylistic cleanup.

## Computer-vision unit tests

Covered within `test_vision_and_safety.py` above rather than a separate
suite (kept together since they share fixtures) — image loading rejection,
preprocessing, and localization transforms are all exercised.

## Robotics unit tests

Covered within `test_rover_and_actuator.py` — state transitions, arrival
detection, emergency stop, and reset are all exercised against the real
`rover_simulator.py` module (no mocking of the state machine itself).

## Frontend

No automated frontend test suite (Vitest/RTL) was added in this sprint —
time was prioritized on backend correctness and end-to-end functionality.
The frontend was instead verified with a scripted Playwright smoke pass
during development (navigate every page, create a demo field, run an
inspection, confirm zero console errors) — see the session notes; this was
a one-off verification script, not a committed test suite. Recommended
follow-up: add Vitest + React Testing Library and a Playwright e2e spec
covering the same flow, checked into `frontend/`.

## Integration / full-workflow test

The core workflow (create field -> inspect image -> detections -> targets
-> approve -> rover navigate -> arrive -> simulated intervention ->
analytics reflect it) is exercised end-to-end by
`test_rover_and_actuator.py::test_rover_navigate_and_arrive` plus the
inspection/target tests, rather than one single mega-test — this keeps
failures localized to the stage that broke.

## Quality gates actually run for this build

- [x] Backend tests pass (31/31)
- [x] Frontend TypeScript compiles clean (`npx tsc -b`)
- [x] Backend imports/starts cleanly (`uvicorn app.main:app`)
- [x] Manual end-to-end walkthrough via API (curl/Invoke-RestMethod) and
      via the browser (Playwright screenshots, zero console errors)
- [ ] Frontend automated test suite — not implemented (see above)
- [ ] Linting (ESLint/ruff) — not configured in this sprint
