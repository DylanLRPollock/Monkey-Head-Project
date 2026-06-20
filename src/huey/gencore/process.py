"""Process bookkeeping for the lightweight kernel."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ProcessDescriptor:
    pid: int
    name: str
    state: str = "created"
    metadata: dict[str, object] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        return {
            "pid": self.pid,
            "name": self.name,
            "state": self.state,
            "metadata": dict(self.metadata),
        }


class ProcessManager:
    """Register and transition logical processes."""

    def __init__(self) -> None:
        self._next_pid = 1000
        self._processes: dict[int, ProcessDescriptor] = {}

    def spawn(
        self, name: str, *, metadata: dict[str, object] | None = None
    ) -> ProcessDescriptor:
        self._next_pid += 1
        process = ProcessDescriptor(
            pid=self._next_pid,
            name=name,
            state="running",
            metadata=dict(metadata or {}),
        )
        self._processes[process.pid] = process
        return process

    def terminate(self, pid: int) -> ProcessDescriptor:
        process = self._processes[pid]
        process.state = "stopped"
        return process

    def mark_waiting(self, pid: int) -> ProcessDescriptor:
        process = self._processes[pid]
        process.state = "waiting"
        return process

    def list_processes(self) -> list[dict[str, object]]:
        return [self._processes[pid].as_dict() for pid in sorted(self._processes)]


__all__ = ["ProcessDescriptor", "ProcessManager"]
