"""WebSocket-style channel fanout for local dashboards."""

from __future__ import annotations


class WebSocketHub:
    """Store the last payload published to each channel."""

    def __init__(self) -> None:
        self._channels: dict[str, list[dict[str, object]]] = {}

    def publish(self, channel: str, payload: dict[str, object]) -> None:
        self._channels.setdefault(channel, []).append(dict(payload))

    def history(self, channel: str) -> list[dict[str, object]]:
        return list(self._channels.get(channel, []))


__all__ = ["WebSocketHub"]
