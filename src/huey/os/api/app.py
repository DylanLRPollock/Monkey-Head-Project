"""Maintained ``hueyos.api`` app entrypoint with legacy compatibility.

This module intentionally re-exports the existing FastAPI application from the
legacy implementation surface while the API is being split into smaller modules.
"""

from __future__ import annotations

from huey.memory.PY import api as _legacy_api

app = _legacy_api.app
main = _legacy_api.main
SCHEDULER = _legacy_api.SCHEDULER

__all__ = ["app", "main", "SCHEDULER"]


def __getattr__(name: str):
    """Delegate unresolved attributes to the legacy API module."""

    return getattr(_legacy_api, name)
