# Auto-generated bridge to legacy module
from __future__ import annotations

from importlib import import_module
from typing import Any

_impl = import_module("huey.memory.PY.pdf_pre_digestion")
__all__ = getattr(
    _impl, "__all__", [name for name in dir(_impl) if not name.startswith("_")]
)
for name in __all__:
    globals()[name] = getattr(_impl, name)


def __getattr__(name: str) -> Any:
    return getattr(_impl, name)


__doc__ = _impl.__doc__
