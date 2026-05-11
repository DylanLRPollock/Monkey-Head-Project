# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: API compatibility wrapper (src)

"""Expose the FastAPI application under :mod:`huey.api`."""

from __future__ import annotations

from .memory.PY import api as _api

# NOTE(v101.1-migration): This module is a compatibility wrapper while
# implementation code remains under ``src/huey/memory/PY``. Do not replace this
# module object via ``sys.modules``; instead re-export legacy symbols explicitly.
app = _api.app
main = _api.main
SCHEDULER = _api.SCHEDULER

__all__ = ["app", "main", "SCHEDULER"]


def __getattr__(name: str):
    """Delegate unknown attributes to the legacy API module for compatibility."""

    return getattr(_api, name)
