"""Compatibility namespace for ``huey.memory.core`` imports."""

from __future__ import annotations

from importlib import import_module
from pkgutil import extend_path
from typing import Iterable

__all__ = ["system_checks"]

__path__ = extend_path(__path__, __name__)


def __getattr__(name: str):  # pragma: no cover - dynamic compatibility shim
    try:
        module = import_module(f"huey.core.{name}")
    except ModuleNotFoundError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    globals()[name] = module
    return module


def __dir__() -> Iterable[str]:  # pragma: no cover
    return sorted(set(__all__) | set(globals()))
