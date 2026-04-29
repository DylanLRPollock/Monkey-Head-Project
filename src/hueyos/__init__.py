"""Compatibility namespace exposing :mod:`huey` as :mod:`hueyos`."""

from __future__ import annotations

import importlib
from typing import Any

_base = importlib.import_module("huey")


def __getattr__(name: str) -> Any:
    return getattr(_base, name)


def __dir__() -> list[str]:
    return sorted(set(dir(_base)))
