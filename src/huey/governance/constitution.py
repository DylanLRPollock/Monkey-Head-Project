"""Constitutional principles for Huey's Cloud Pyramid governance model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Principle:
    name: str
    statement: str
    weight: float = 1.0


class HueyConstitution:
    """Provide the base set of governance principles."""

    def __init__(self, principles: list[Principle] | None = None) -> None:
        self._principles = principles or [
            Principle("safety", "Protect humans, hardware, and data integrity.", 1.3),
            Principle("transparency", "Leave clear traces of decisions and actions."),
            Principle("resilience", "Prefer reversible and fault-tolerant actions.", 1.1),
            Principle("autonomy", "Empower local operation before external dependency."),
        ]

    def principles(self) -> list[Principle]:
        return list(self._principles)

    def summary(self) -> list[dict[str, object]]:
        return [
            {
                "name": principle.name,
                "statement": principle.statement,
                "weight": principle.weight,
            }
            for principle in self._principles
        ]


__all__ = ["HueyConstitution", "Principle"]
