"""Performance and operational metrics registry."""

from __future__ import annotations


class MetricsRegistry:
    """Track counters and gauges in a serializable registry."""

    def __init__(self) -> None:
        self._metrics: dict[str, float] = {}

    def increment(self, name: str, amount: float = 1.0) -> float:
        self._metrics[name] = self._metrics.get(name, 0.0) + amount
        return self._metrics[name]

    def set(self, name: str, value: float) -> float:
        self._metrics[name] = value
        return value

    def snapshot(self) -> dict[str, float]:
        return dict(self._metrics)


__all__ = ["MetricsRegistry"]
