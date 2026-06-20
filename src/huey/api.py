# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: API compatibility wrapper (src)

"""Expose the FastAPI application under :mod:`huey.api`."""

from __future__ import annotations

import sys
from importlib import import_module

_impl = import_module("huey.memory.PY.api")
sys.modules[__name__] = _impl
