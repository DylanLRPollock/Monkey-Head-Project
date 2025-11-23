"""Compatibility namespace for legacy ``huey.memory`` modules."""

from __future__ import annotations

import importlib
from typing import Iterable

__all__: list[str] = ["PY"]


def __getattr__(name: str):  # pragma: no cover - thin import wrapper
    """Dynamically resolve submodules shipped with HueyOS."""

    try:
        module = importlib.import_module(f"{__name__}.PY.{name}")
    except ModuleNotFoundError as exc:  # pragma: no cover - error propagation
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    globals()[name] = module
    return module


def __dir__() -> Iterable[str]:  # pragma: no cover - convenience helper
    return sorted(set(__all__) | set(globals()))
