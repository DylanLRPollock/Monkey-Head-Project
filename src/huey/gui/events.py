"""Small event bus used by GUI-facing Python components."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Callable
from uuid import uuid4

EventCallback = Callable[["Event"], None]


def _utc_now() -> str:
    return datetime.now(tz=UTC).isoformat()


class EventType(StrEnum):
    MEMORY_UPDATED = "memory_updated"
    TRANSCRIPTION_COMPLETE = "transcription_complete"
    RUN_STARTED = "run_started"
    RUN_FINISHED = "run_finished"
    API_CONNECTED = "api_connected"
    MODEL_CHANGED = "model_changed"
    REPOSITORY_CHANGED = "repository_changed"


@dataclass(frozen=True)
class Event:
    event_type: EventType
    payload: dict[str, object] = field(default_factory=dict)
    source: str = ""
    timestamp: str = field(default_factory=_utc_now)
    event_id: str = field(default_factory=lambda: uuid4().hex)


class EventBus:
    """In-process publish/subscribe event bus for GUI state sharing."""

    def __init__(self) -> None:
        self._subscribers: dict[EventType, list[EventCallback]] = {
            event_type: [] for event_type in EventType
        }
        self._history: list[Event] = []

    def subscribe(self, event_type: EventType | str, callback: EventCallback) -> None:
        self._subscribers[self._normalise(event_type)].append(callback)

    def unsubscribe(self, event_type: EventType | str, callback: EventCallback) -> None:
        subscribers = self._subscribers[self._normalise(event_type)]
        if callback in subscribers:
            subscribers.remove(callback)

    def emit(
        self,
        event_type: Event | EventType | str,
        payload: dict[str, object] | None = None,
        *,
        source: str = "",
    ) -> Event:
        if isinstance(event_type, Event):
            event = event_type
        else:
            event = Event(
                event_type=self._normalise(event_type),
                payload=dict(payload or {}),
                source=source,
            )
        self._history.append(event)
        for callback in list(self._subscribers[event.event_type]):
            callback(event)
        return event

    def history(self, event_type: EventType | str | None = None) -> list[Event]:
        if event_type is None:
            return list(self._history)
        selected = self._normalise(event_type)
        return [event for event in self._history if event.event_type == selected]

    @staticmethod
    def _normalise(event_type: EventType | str) -> EventType:
        if isinstance(event_type, EventType):
            return event_type
        return EventType(event_type.strip().lower())


__all__ = ["Event", "EventBus", "EventType"]
