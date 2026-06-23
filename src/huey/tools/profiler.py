"""Minimal profiling helpers for timing critical sections."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter


@dataclass(slots=True)
class ProfileTimer:
    label: str
    started_at: float = field(default_factory=perf_counter)
    finished_at: float | None = None

    def stop(self) -> float:
        self.finished_at = perf_counter()
        return self.elapsed

    @property
    def elapsed(self) -> float:
        end = perf_counter() if self.finished_at is None else self.finished_at
        return end - self.started_at


__all__ = ["ProfileTimer"]
