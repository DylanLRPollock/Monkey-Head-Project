"""Compatibility layer for service management helpers."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import List

_base = import_module("huey.services")

__all__ = list(getattr(_base, "__all__", ()))

for name in list(__all__):
    globals()[name] = import_module(f"huey.services.{name}")

# Expose the compatibility modules implemented in this package as part of the
# public API so that ``from monkey_head.services import environment_setup`` works
# as it did historically.
__all__.extend(["environment_setup", "home_assistant"])

environment_setup = import_module("monkey_head.services.environment_setup")
home_assistant = import_module("monkey_head.services.home_assistant")

__path__: List[str] = [str(Path(__file__).resolve().parent)]
for candidate in getattr(_base, "__path__", []):
    if candidate not in __path__:
        __path__.append(candidate)
