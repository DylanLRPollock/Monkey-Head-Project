"""Expose utility helpers for :mod:`huey.memory` consumers."""

from __future__ import annotations

import importlib
from typing import Iterable

__all__ = ["commands", "logger"]


def __getattr__(name: str):  # pragma: no cover - dynamic compatibility shim
    try:
        module = importlib.import_module(f"{__name__}.{name}")
    except ModuleNotFoundError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    globals()[name] = module
    return module


def __dir__() -> Iterable[str]:  # pragma: no cover
    return sorted(set(__all__) | set(globals()))
