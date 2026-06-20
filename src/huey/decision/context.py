"""Context objects passed into decision and agent flows."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class DecisionContext:
    goal: str
    signals: dict[str, float] = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)

    def signal_score(self) -> float:
        if not self.signals:
            return 0.0
        return sum(self.signals.values()) / len(self.signals)


__all__ = ["DecisionContext"]
