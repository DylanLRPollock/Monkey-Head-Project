"""Entry point wrapper for the legacy :mod:`monkey_head.run` module."""

from __future__ import annotations

from importlib import import_module
from typing import Any, Callable

_module = import_module("monkey_head.run")

__all__ = getattr(_module, "__all__", [name for name in dir(_module) if not name.startswith("_")])
for _name in ("main", "launch_gui", "launch_manager_ui", "_load_cli"):
    if _name not in __all__:
        __all__.append(_name)

_launch_manager_ui_impl: Callable[..., Any] = getattr(_module, "launch_manager_ui")
_launch_gui_impl: Callable[..., Any] = getattr(_module, "launch_gui")
_load_cli_impl: Callable[..., Any] = getattr(_module, "_load_cli")


def __getattr__(name: str) -> Any:  # pragma: no cover - proxy
    return getattr(_module, name)


def launch_manager_ui(*args: Any, **kwargs: Any) -> Any:
    """Proxy to the real ``launch_manager_ui`` implementation."""

    return _launch_manager_ui_impl(*args, **kwargs)


def launch_gui(*args: Any, **kwargs: Any) -> Any:
    """Proxy to the real ``launch_gui`` implementation."""

    return _launch_gui_impl(*args, **kwargs)


def _load_cli(*args: Any, **kwargs: Any) -> Any:
    """Proxy to the real ``_load_cli`` implementation."""

    return _load_cli_impl(*args, **kwargs)


def main(*args: Any, **kwargs: Any) -> Any:
    """Invoke :func:`monkey_head.run.main` with patched hooks."""

    setattr(_module, "launch_manager_ui", globals()["launch_manager_ui"])
    setattr(_module, "launch_gui", globals()["launch_gui"])
    setattr(_module, "_load_cli", globals()["_load_cli"])
    return _module.main(*args, **kwargs)
