"""Power distribution management for Huey's embodied hardware."""

from __future__ import annotations


class PowerController:
    """Track subsystem power budgets and aggregate draw."""

    def __init__(self, *, budget_watts: float = 500.0) -> None:
        self.budget_watts = budget_watts
        self._allocations: dict[str, float] = {}

    def allocate(self, subsystem: str, watts: float) -> dict[str, object]:
        self._allocations[subsystem] = watts
        return {"subsystem": subsystem, "watts": watts, "remaining": self.remaining_watts}

    @property
    def remaining_watts(self) -> float:
        return round(self.budget_watts - sum(self._allocations.values()), 2)

    def snapshot(self) -> dict[str, object]:
        return {"budget_watts": self.budget_watts, "allocations": dict(self._allocations)}


__all__ = ["PowerController"]
