"""Sensor access helpers layered on top of the existing manager types."""

from __future__ import annotations

from .manager import SensorManager, create_default_sensor_manager


class SensorHub:
    """High-level helper for polling sensor state."""

    def __init__(self, manager: SensorManager | None = None) -> None:
        self.manager = manager or create_default_sensor_manager()

    def inventory(self) -> list[dict[str, object]]:
        return self.manager.list_sensors()

    def poll_all(self) -> list[dict[str, object]]:
        return [
            {
                "name": reading.name,
                "value": reading.value,
                "timestamp": reading.timestamp,
                "provenance": reading.provenance,
            }
            for reading in self.manager.poll_all()
        ]


__all__ = ["SensorHub"]
