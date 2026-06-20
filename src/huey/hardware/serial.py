"""Serial communication abstractions for sensor and actuator buses."""

from __future__ import annotations


class SerialBus:
    """Register endpoints and retain the most recent payload per port."""

    def __init__(self) -> None:
        self._ports: dict[str, str] = {}

    def send(self, port: str, payload: str) -> dict[str, object]:
        self._ports[port] = payload
        return {"port": port, "payload": payload}

    def receive(self, port: str) -> str | None:
        return self._ports.get(port)

    def snapshot(self) -> dict[str, str]:
        return dict(self._ports)


__all__ = ["SerialBus"]
