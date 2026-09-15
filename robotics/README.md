# robotics/

The rover simulator, safety gate, and actuator abstraction are implemented in
`backend/app/services/rover_simulator.py`, `safety.py`, and `actuator.py`
respectively (kept alongside the API so state persists to the same
database). This directory documents the design; see those files for the
runnable implementation.

## Simulation model

- **Pull-based physics**: rather than a background thread ticking
  continuously, position is advanced whenever the rover's state is read or
  acted upon, using real elapsed wall-clock time since the last update
  (capped at 2s per tick to avoid large jumps after idle periods). This
  keeps the implementation simple and avoids threads contending with
  SQLite, while still producing genuine time-based movement — verified in
  `backend/tests/test_rover_and_actuator.py::test_rover_navigate_and_arrive`.
- **State machine**: `IDLE -> READY -> NAVIGATING -> ARRIVED ->
  INTERVENTION_PENDING -> INTERVENTING -> COMPLETED`, plus `PAUSED`,
  `STOPPED`, `SAFETY_LOCK`, `ERROR`.
- **Safety gate** (`safety.py`): every actuation (and, implicitly, every
  navigation command) is checked against confidence, localization validity,
  restricted/crop-protection zones, rover speed, emergency-stop state, and
  operator approval. All checks are real boolean evaluations against the
  target/session/settings state — nothing here is decorative.
- **Actuator** (`actuator.py`): `SimulatedActuator` performs a harmless,
  purely virtual "mark target as treated" action. `HardwareActuator` is a
  documented but unimplemented interface (raises `NotImplementedError`) —
  see `docs/HARDWARE_INTEGRATION.md` for what a real implementation would
  need to do.

## What this simulation does NOT prove

Simulated navigation does not validate real-world path planning, terrain
handling, sensor fusion, or actuator timing. See
`docs/HARDWARE_INTEGRATION.md` for the gap between this software simulation
and a safe physical deployment.
