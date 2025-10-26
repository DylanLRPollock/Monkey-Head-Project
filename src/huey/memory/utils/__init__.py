"""Expose legacy utility helpers for :mod:`huey.memory` consumers."""

from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path
from pkgutil import extend_path
from typing import Iterable

__all__ = ["commands", "logger"]

__path__ = extend_path(__path__, __name__)

_project_root = Path(__file__).resolve().parents[3]
_legacy_root = _project_root / "huey" / "memory" / "PY"
if _legacy_root.exists():
    legacy_path = str(_legacy_root)
    if isinstance(__path__, list):
        search_path: list[str] = __path__
    else:  # pragma: no cover - defensive fallback
        search_path = list(__path__)  # type: ignore[arg-type]
    if legacy_path not in search_path:
        search_path.append(legacy_path)
        __path__ = search_path  # type: ignore[assignment]
    if legacy_path not in sys.path:
        sys.path.insert(0, legacy_path)


def __getattr__(name: str):  # pragma: no cover - dynamic compatibility shim
    try:
        module = import_module(f"huey.memory.PY.{name}")
    except ModuleNotFoundError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    globals()[name] = module
    return module


def __dir__() -> Iterable[str]:  # pragma: no cover
    return sorted(set(__all__) | set(globals()))
