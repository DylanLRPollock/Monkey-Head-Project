"""Lightweight integration adapter for the vendored PyHuey surface."""

from __future__ import annotations

from collections import deque
from typing import Iterable

from huey.pygpt_integration import pyhuey_status

from .app import get_last_launch_state, run as run_app

_EVENT_QUEUE: deque[dict[str, object]] = deque()
_RUNNING = False


def launch_pyhuey(*, tools: Iterable[object] | None = None) -> dict[str, object]:
    """Launch the PyHuey surface with optional HueyOS tools."""

    global _RUNNING
    run_app(tools=tools)
    _RUNNING = True
    return get_status()


def shutdown_pyhuey() -> dict[str, object]:
    """Mark the PyHuey adapter as stopped."""

    global _RUNNING
    _RUNNING = False
    return get_status()


def send_event(
    event_type: str, payload: dict[str, object] | None = None
) -> dict[str, object]:
    """Queue an event for the PyHuey integration surface."""

    event = {"event_type": event_type, "payload": dict(payload or {})}
    _EVENT_QUEUE.append(event)
    return event


def receive_event() -> dict[str, object] | None:
    """Receive the next queued PyHuey event if one exists."""

    if not _EVENT_QUEUE:
        return None
    return _EVENT_QUEUE.popleft()


def get_status() -> dict[str, object]:
    """Return adapter and discovery status for PyHuey integration."""

    payload = dict(pyhuey_status())
    payload.update(
        {
            "running": _RUNNING,
            "queued_events": len(_EVENT_QUEUE),
            "ready": bool(payload.get("prepared")),
        }
    )
    payload["gui_state"] = get_last_launch_state()
    if _EVENT_QUEUE:
        payload["last_event"] = _EVENT_QUEUE[-1]
    return payload


__all__ = [
    "get_status",
    "launch_pyhuey",
    "receive_event",
    "send_event",
    "shutdown_pyhuey",
]
