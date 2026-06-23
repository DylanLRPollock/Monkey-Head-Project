"""Cooling control helpers for robotics and edge workloads."""

from __future__ import annotations


class CoolingController:
    """Maintain a target thermal profile."""

    def __init__(self, *, target_celsius: float = 55.0) -> None:
        self.target_celsius = target_celsius
        self.fan_percent = 40.0

    def adjust(self, *, current_celsius: float) -> dict[str, float]:
        delta = current_celsius - self.target_celsius
        self.fan_percent = min(100.0, max(20.0, self.fan_percent + delta))
        return {
            "target_celsius": self.target_celsius,
            "current_celsius": current_celsius,
            "fan_percent": round(self.fan_percent, 2),
        }


__all__ = ["CoolingController"]
