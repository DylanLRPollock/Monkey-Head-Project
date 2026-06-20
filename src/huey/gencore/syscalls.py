"""System-call registry for higher-level HueyOS services."""

from __future__ import annotations

from typing import Any, Callable

SyscallHandler = Callable[..., Any]


class SyscallRegistry:
    """Map symbolic syscall names to Python callables."""

    def __init__(self) -> None:
        self._handlers: dict[str, SyscallHandler] = {}

    def register(self, name: str, handler: SyscallHandler) -> None:
        self._handlers[name] = handler

    def invoke(self, name: str, *args: object, **kwargs: object) -> Any:
        return self._handlers[name](*args, **kwargs)

    def list_syscalls(self) -> list[str]:
        return sorted(self._handlers)


__all__ = ["SyscallHandler", "SyscallRegistry"]
