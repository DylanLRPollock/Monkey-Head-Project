"""Lightweight shim providing access to mirrored PyGPT components."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any
import sys

__all__ = ["__getattr__", "__dir__"]

_PYGPT_PACKAGE: ModuleType | None = None


def _prepare_sys_path() -> None:
    project_root = Path(__file__).resolve().parents[1]
    candidates = [
        project_root / "pygpt" / "src",
        project_root / "pygpt",
        project_root / "repo" / "pygpt-MHP" / "src",
    ]
    for path in candidates:
        if path.exists():
            resolved = str(path.resolve())
            if resolved not in sys.path:
                sys.path.insert(0, resolved)


def _load_package() -> ModuleType:
    global _PYGPT_PACKAGE
    if _PYGPT_PACKAGE is None:
        _prepare_sys_path()
        _PYGPT_PACKAGE = import_module("pygpt_net")
    return _PYGPT_PACKAGE


def __getattr__(name: str) -> Any:
    return getattr(_load_package(), name)


def __dir__() -> list[str]:  # pragma: no cover - convenience helper
    package = _load_package()
    return sorted(set(globals()) | set(dir(package)))
