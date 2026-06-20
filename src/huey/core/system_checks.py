# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: System Checks module (huey/core)

"""Compatibility layer exposing ``huey.system_checks`` under ``huey.core``."""

from __future__ import annotations

import sys
from importlib import import_module

_impl = import_module("huey.system_checks")
sys.modules[__name__] = _impl
