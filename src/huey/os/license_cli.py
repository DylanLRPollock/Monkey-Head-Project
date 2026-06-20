"""Alias the maintained license CLI implementation under :mod:`hueyos`."""

from __future__ import annotations

import sys
from importlib import import_module

_impl = import_module("huey.memory.PY.license_cli")
sys.modules[__name__] = _impl
