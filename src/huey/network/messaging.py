"""Message queue helpers for inter-service communication."""

from __future__ import annotations

from .protocol import ProtocolEnvelope


class MessageQueue:
    """FIFO queue for protocol envelopes."""

    def __init__(self) -> None:
        self._queue: list[ProtocolEnvelope] = []

    def publish(self, envelope: ProtocolEnvelope) -> None:
        self._queue.append(envelope)

    def consume(self) -> ProtocolEnvelope | None:
        if not self._queue:
            return None
        return self._queue.pop(0)

    def pending(self) -> list[str]:
        return [envelope.topic for envelope in self._queue]


__all__ = ["MessageQueue"]
