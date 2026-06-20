"""Interrupt routing for GenCore subsystems."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

InterruptHandler = Callable[["Interrupt"], object]


@dataclass(slots=True)
class Interrupt:
    code: str
    source: str
    payload: dict[str, object] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        return {"code": self.code, "source": self.source, "payload": dict(self.payload)}


class InterruptController:
    """Register and dispatch named interrupts."""

    def __init__(self) -> None:
        self._handlers: dict[str, InterruptHandler] = {}
        self._history: list[Interrupt] = []

    def register_handler(self, code: str, handler: InterruptHandler) -> None:
        self._handlers[code] = handler

    def dispatch(self, interrupt: Interrupt) -> object | None:
        self._history.append(interrupt)
        handler = self._handlers.get(interrupt.code)
        if handler is None:
            return None
        return handler(interrupt)

    def history(self) -> list[dict[str, object]]:
        return [interrupt.as_dict() for interrupt in self._history]


__all__ = ["Interrupt", "InterruptController"]
