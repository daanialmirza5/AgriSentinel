"""Actuator abstraction.

Only ``SimulatedActuator`` is implemented in this MVP - it performs a
harmless, purely virtual "mark target as treated" action and never touches
any real hardware. ``HardwareActuator`` documents the interface a future
physical sprayer/marker driver would implement; instantiating it raises
NotImplementedError so it can never be silently mistaken for a working
integration. See docs/HARDWARE_INTEGRATION.md.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any


@dataclass
class ActuatorTarget:
    target_id: str
    field_x: float | None
    field_y: float | None


class Actuator:
    def execute(self, target: ActuatorTarget) -> dict[str, Any]:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError


class SimulatedActuator(Actuator):
    """Virtual marker: records a timestamped simulated treatment event.
    Performs no physical action of any kind.
    """

    def __init__(self) -> None:
        self._stopped = False

    def execute(self, target: ActuatorTarget) -> dict[str, Any]:
        if self._stopped:
            return {"success": False, "reason": "actuator_stopped"}
        return {
            "success": True,
            "action_type": "simulated_marker",
            "target_id": target.target_id,
            "field_x": target.field_x,
            "field_y": target.field_y,
            "executed_at": dt.datetime.utcnow().isoformat(),
            "note": "Simulated action only. No physical treatment was applied.",
        }

    def stop(self) -> None:
        self._stopped = True

    def reset(self) -> None:
        self._stopped = False


class HardwareActuator(Actuator):
    """Documented extension point for a real sprayer/marker driver.

    A future implementation would, for example, open a serial/GPIO
    connection to a solenoid or servo controller and translate
    ``target.field_x/field_y`` into an actuation command once the rover is
    physically positioned. This class intentionally raises
    NotImplementedError so the application can never claim a hardware
    connection that does not exist.
    """

    def execute(self, target: ActuatorTarget) -> dict[str, Any]:
        raise NotImplementedError("HardwareActuator is not implemented in this build. See docs/HARDWARE_INTEGRATION.md")

    def stop(self) -> None:
        raise NotImplementedError("HardwareActuator is not implemented in this build. See docs/HARDWARE_INTEGRATION.md")


simulated_actuator = SimulatedActuator()
