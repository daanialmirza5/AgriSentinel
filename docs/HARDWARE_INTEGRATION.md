# Hardware Integration Roadmap

AgriSentinel is simulation-first. Nothing in this build controls or is
connected to physical hardware. This document describes what a future
physical integration would need — it is a roadmap, not a claim of readiness.

## Hardware abstraction points already in the code

| Concern | Interface | Simulated implementation | Hardware implementation |
|---|---|---|---|
| Camera | OpenCV `VideoCapture` (device index) | `camera_manager.py` uses a real local webcam if present | Same code works with a USB/CSI camera; no change needed beyond device index/URL |
| Rover movement | `rover_simulator.py` functions operating on `RoverSession` | Time-based 2D position update | Replace `_advance()`'s position math with real odometry/encoder feedback, or drive a motor controller from the same navigate/pause/stop/emergency-stop call sites |
| Actuator | `Actuator` ABC (`actuator.py`) | `SimulatedActuator` (virtual marker only) | `HardwareActuator` — currently raises `NotImplementedError`; must be implemented against real solenoid/servo/sprayer control hardware |
| Localization | `localization.py::pixel_to_field()` | Simulated ground-plane scaling | Real camera calibration / homography / GNSS fusion — see `docs/CALIBRATION.md` |
| Safety | `safety.py::evaluate_target_safety()` | Software checks only | Must be paired with an independent hardware emergency-stop circuit (see below) |

## Suggested physical stack (not required for this MVP)

- Rover chassis (differential-drive or tracked) sized for row spacing.
- Edge compute: Raspberry Pi 4/5 or NVIDIA Jetson (Orin Nano/Nano) for
  onboard inference if not tethered to a laptop.
- Camera: USB or CSI, ideally global-shutter for motion blur resistance.
- Motor controller with encoder feedback for real odometry.
- Servo or solenoid for the physical marker/sprayer mechanism.
- Battery + power distribution sized for the compute + motors.
- **Independent, hardware emergency-stop switch** wired directly to motor
  power, not solely through software — see below.
- Optional: depth camera or ultrasonic sensors for obstacle detection;
  GNSS/RTK receiver for outdoor absolute positioning instead of the
  simulated ground-plane mapping.

## Simulation-to-hardware migration path

1. Implement `HardwareActuator.execute()`/`stop()` against your real
   actuation hardware (serial/GPIO/CAN — whatever your controller speaks).
2. Swap `SimulatedActuator` for `HardwareActuator` behind a config flag;
   keep the exact same `safety.evaluate_target_safety()` gate in front of
   it — do not bypass it for hardware.
3. Replace `rover_simulator._advance()`'s position integration with real
   odometry reads, and its "move toward target" logic with your actual
   motor-control commands, keeping the same state machine and event log so
   the frontend and database schema need no changes.
4. Calibrate the camera and switch `localization.py` to Option A or C (see
   `docs/CALIBRATION.md`) before trusting field coordinates for real
   actuation.
5. Re-run the full safety test suite (`backend/tests/test_rover_and_actuator.py`)
   against the hardware-backed implementation, then add hardware-in-the-loop
   tests before any unsupervised field operation.

## Safety requirements for physical deployment (not satisfied by this software)

- **Simulation does not prove real-world safety.** Passing every test in
  this repository proves the *software logic* is internally consistent; it
  proves nothing about real terrain, real actuator timing, or real sensor
  noise.
- Outdoor terrain (slopes, mud, uneven rows) changes the navigation problem
  entirely; the flat, obstacle-rectangle 2D model here does not transfer.
  A real navigation stack needs terrain sensing and slip-aware control.
- Camera calibration must be physically validated (see
  `docs/CALIBRATION.md`), not assumed from the simulated mapping.
  Actuator positioning/timing must be tested against real target
  geometry and rover speed before any live trial.
- Autonomous field operation requires structured field testing with a human
  supervisor able to trigger the **hardware** emergency stop at all times.
  A software-only emergency stop is not sufficient for physical safety —
  wire a physical, motor-power-cutting emergency stop switch independent of
  the compute stack.
- Chemical spraying (if ever implemented) requires additional regulatory,
  environmental, and safety review well beyond this software's scope. This
  prototype must **not** be used for unsupervised chemical application.
