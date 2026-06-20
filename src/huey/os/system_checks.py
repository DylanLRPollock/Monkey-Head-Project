"""Compatibility shim exposing ``huey.system_checks`` under ``huey.os``."""

from __future__ import annotations

import sys
from importlib import import_module

_impl = import_module("huey.system_checks")
sys.modules[__name__] = _impl
