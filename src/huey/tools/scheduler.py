"""Cron-like scheduling helpers using simple interval checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Callable

JobHandler = Callable[[], object]


@dataclass(slots=True)
class ScheduledJob:
    name: str
    every_seconds: int
    handler: JobHandler
    last_run: float = field(default=0.0)

    def due(self, now: float | None = None) -> bool:
        current = time() if now is None else now
        return current - self.last_run >= self.every_seconds


class JobScheduler:
    """Run interval jobs when they become due."""

    def __init__(self) -> None:
        self._jobs: list[ScheduledJob] = []

    def register(self, job: ScheduledJob) -> None:
        self._jobs.append(job)

    def tick(self, *, now: float | None = None) -> list[dict[str, object]]:
        current = time() if now is None else now
        results: list[dict[str, object]] = []
        for job in self._jobs:
            if not job.due(current):
                continue
            result = job.handler()
            job.last_run = current
            results.append({"name": job.name, "result": result, "ran_at": current})
        return results


__all__ = ["JobScheduler", "ScheduledJob"]
