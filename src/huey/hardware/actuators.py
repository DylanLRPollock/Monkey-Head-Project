"""Actuator control helpers layered on the existing manager types."""

from __future__ import annotations

from .manager import ActuatorManager, create_default_actuator_manager


class ActuatorHub:
    """High-level helper for invoking actuator commands."""

    def __init__(self, manager: ActuatorManager | None = None) -> None:
        self.manager = manager or create_default_actuator_manager()

    def inventory(self) -> list[dict[str, object]]:
        return self.manager.list_actuators()

    def command(
        self,
        actuator_name: str,
        operation: str,
        payload: dict[str, object] | None = None,
    ) -> dict[str, object]:
        result = self.manager.perform(actuator_name, operation, payload)
        return {"actuator": actuator_name, "operation": operation, "result": result}


__all__ = ["ActuatorHub"]
