# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: PyHuey integration compatibility wrapper (src)

"""Expose PyHuey integration utilities under :mod:`huey.pyhuey_integration`."""

from __future__ import annotations

from .memory.PY import pygpt_integration as _pyhuey_integration

__all__ = list(getattr(_pyhuey_integration, "__all__", ()))

globals().update({name: getattr(_pyhuey_integration, name) for name in __all__})
