"""Task scheduling primitives for GenCore."""

from __future__ import annotations

from dataclasses import dataclass, field
from heapq import heappop, heappush
from typing import Callable

TaskHandler = Callable[[dict[str, object]], object]


@dataclass(order=True, slots=True)
class ScheduledTask:
    priority: int
    order: int
    name: str = field(compare=False)
    payload: dict[str, object] = field(default_factory=dict, compare=False)
    handler: TaskHandler | None = field(default=None, compare=False)
    status: str = field(default="pending", compare=False)
    result: object | None = field(default=None, compare=False)

    def as_dict(self) -> dict[str, object]:
        return {
            "priority": self.priority,
            "name": self.name,
            "payload": dict(self.payload),
            "status": self.status,
            "result": self.result,
        }


class TaskScheduler:
    """Priority scheduler for kernel and tooling jobs."""

    def __init__(self) -> None:
        self._queue: list[ScheduledTask] = []
        self._counter = 0

    def schedule(
        self,
        name: str,
        *,
        priority: int = 100,
        payload: dict[str, object] | None = None,
        handler: TaskHandler | None = None,
    ) -> ScheduledTask:
        self._counter += 1
        task = ScheduledTask(
            priority=priority,
            order=self._counter,
            name=name,
            payload=dict(payload or {}),
            handler=handler,
        )
        heappush(self._queue, task)
        return task

    def pending(self) -> list[ScheduledTask]:
        return sorted(self._queue)

    def run_next(self) -> ScheduledTask | None:
        if not self._queue:
            return None
        task = heappop(self._queue)
        task.status = "running"
        task.result = None if task.handler is None else task.handler(task.payload)
        task.status = "completed"
        return task

    def run_all(self, *, limit: int | None = None) -> list[ScheduledTask]:
        completed: list[ScheduledTask] = []
        while self._queue and (limit is None or len(completed) < limit):
            task = self.run_next()
            if task is not None:
                completed.append(task)
        return completed


__all__ = ["ScheduledTask", "TaskHandler", "TaskScheduler"]
