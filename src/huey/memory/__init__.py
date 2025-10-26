"""Compatibility namespace for legacy ``huey.memory`` modules."""

from __future__ import annotations

import sys
from pathlib import Path
from pkgutil import extend_path
from typing import Iterable

__all__: list[str] = ["PY"]

# Start with the standard namespace package path.
__path__ = extend_path(__path__, __name__)

_project_root = Path(__file__).resolve().parents[2]
_legacy_root = _project_root / "huey" / "memory"
if _legacy_root.exists():
    legacy_path = str(_legacy_root)
    # ``extend_path`` may return a list or a specialised iterable depending on
    # the environment. Normalise to a mutable list so we can append our legacy
    # sources without duplicating entries across interpreter restarts.
    if isinstance(__path__, list):
        search_path: list[str] = __path__
    else:  # pragma: no cover - extremely defensive fallback
        search_path = list(__path__)  # type: ignore[arg-type]
    if legacy_path not in search_path:
        search_path.append(legacy_path)
        __path__ = search_path  # type: ignore[assignment]
    if legacy_path not in sys.path:
        sys.path.insert(0, legacy_path)


def __getattr__(name: str):  # pragma: no cover - thin import wrapper
    """Dynamically resolve submodules from the legacy tree."""

    import importlib

    try:
        module = importlib.import_module(f"huey.memory.PY.{name}")
    except ModuleNotFoundError as exc:  # pragma: no cover - error propagation
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    globals()[name] = module
    return module


def __dir__() -> Iterable[str]:  # pragma: no cover - convenience helper
    return sorted(set(__all__) | set(globals()))
