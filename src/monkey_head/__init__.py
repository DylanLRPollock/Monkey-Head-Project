"""Compatibility namespace for legacy Monkey Head modules.

The original Monkey Head codebase stored many modules under
``huey/memory/PY``.  Some environments still import them via the
``monkey_head`` prefix, so this package maps that namespace onto the
existing source tree.  It mirrors the lightweight discovery helpers
used by :mod:`hueyos` to keep imports working without depending on
external packages.
"""
from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path
from typing import Iterable, Set

_PACKAGE_ROOT = Path(__file__).resolve().parent
_SRC_ROOT = _PACKAGE_ROOT.parents[1]
_HUEY_ROOT = _SRC_ROOT / "huey"
_LEGACY_ROOT = _HUEY_ROOT / "memory" / "PY"

__path__ = [str(_PACKAGE_ROOT)]
for candidate in (_HUEY_ROOT, _LEGACY_ROOT):
    if candidate.exists():
        __path__.append(str(candidate))

if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))


def _discover_exports(paths: Iterable[str]) -> Set[str]:
    names: Set[str] = set()
    for entry in paths:
        base = Path(entry)
        if not base.exists():
            continue
        for item in base.iterdir():
            if item.name.startswith("_"):
                continue
            if item.is_dir() and (item / "__init__.py").exists():
                names.add(item.name)
            elif item.suffix == ".py":
                names.add(item.stem)
    return names


__all__ = sorted(_discover_exports(__path__))


def __getattr__(name: str):  # pragma: no cover - thin import wrapper
    for target in (
        f"monkey_head.{name}",
        f"huey.{name}",
        f"huey.memory.PY.{name}",
    ):
        try:
            module = import_module(target)
        except ModuleNotFoundError:
            continue
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:  # pragma: no cover - convenience helper
    return sorted(set(__all__) | set(globals()))
