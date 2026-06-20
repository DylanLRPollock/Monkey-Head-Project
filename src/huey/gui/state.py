"""Shared GUI state containers for HueyOS surfaces."""

from __future__ import annotations

from dataclasses import dataclass, field

from huey.gui.defaults import default_repositories
from huey.gui.events import Event, EventType
from huey.gui.models import RepoStatus, dataclass_to_dict
from huey.utils.paths import get_memory_path


def _default_memory_root() -> str:
    return str(get_memory_path(create=True))


@dataclass
class OperatorState:
    active_view: str = "overview"
    selected_phase_id: str = ""
    selected_repository: str = "DylanLRPollock/Monkey-Head-Project"
    mock_only: bool = True


@dataclass
class RuntimeState:
    orchestration_status: str = "idle"
    health_status: str = "unknown"
    api_connected: bool = False
    active_model: str = ""
    services: dict[str, dict[str, object]] = field(default_factory=dict)
    pipelines: dict[str, dict[str, object]] = field(default_factory=dict)
    models: dict[str, dict[str, object]] = field(default_factory=dict)


@dataclass
class MemoryState:
    root_path: str = field(default_factory=_default_memory_root)
    data_mode: str = "local"
    last_update: str = ""
    indexed_documents: int = 0
    last_query: str = ""


@dataclass
class RepositoryState:
    repositories: list[RepoStatus] = field(default_factory=default_repositories)
    active_repository: str = "DylanLRPollock/Monkey-Head-Project"


@dataclass
class HueyState:
    operator: OperatorState = field(default_factory=OperatorState)
    runtime: RuntimeState = field(default_factory=RuntimeState)
    memory: MemoryState = field(default_factory=MemoryState)
    repositories: RepositoryState = field(default_factory=RepositoryState)
    recent_events: list[Event] = field(default_factory=list)

    def apply_event(self, event: Event) -> None:
        self.recent_events.append(event)
        if event.event_type is EventType.API_CONNECTED:
            self.runtime.api_connected = True
            self.runtime.health_status = str(event.payload.get("status", "connected"))
        elif event.event_type is EventType.RUN_STARTED:
            self.runtime.orchestration_status = "running"
        elif event.event_type is EventType.RUN_FINISHED:
            self.runtime.orchestration_status = str(event.payload.get("status", "idle"))
        elif event.event_type is EventType.MEMORY_UPDATED:
            self.memory.last_update = event.timestamp
            self.memory.indexed_documents = int(
                event.payload.get("indexed_documents", self.memory.indexed_documents)
            )
        elif event.event_type is EventType.MODEL_CHANGED:
            self.runtime.active_model = str(event.payload.get("model", ""))
        elif event.event_type is EventType.REPOSITORY_CHANGED:
            selected = str(event.payload.get("repository", ""))
            if selected:
                self.operator.selected_repository = selected
                self.repositories.active_repository = selected

    def as_dict(self) -> dict[str, object]:
        return dataclass_to_dict(self)


def build_default_state() -> HueyState:
    """Return the canonical default GUI state."""

    return HueyState()


__all__ = [
    "HueyState",
    "MemoryState",
    "OperatorState",
    "RepositoryState",
    "RuntimeState",
    "build_default_state",
]
