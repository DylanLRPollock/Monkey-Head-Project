"""Adaptive UI profile selection for differing operator preferences."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AdaptiveUIProfile:
    name: str
    density: str
    emphasis: str


class AdaptiveUIEngine:
    """Select a UI profile based on task focus and operator preference."""

    def choose(self, *, mode: str, operator: str = "default") -> AdaptiveUIProfile:
        if mode == "diagnostics":
            return AdaptiveUIProfile(operator, density="compact", emphasis="telemetry")
        if mode == "control":
            return AdaptiveUIProfile(operator, density="balanced", emphasis="actions")
        return AdaptiveUIProfile(operator, density="comfortable", emphasis="summary")


__all__ = ["AdaptiveUIEngine", "AdaptiveUIProfile"]
