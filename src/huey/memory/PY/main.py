# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Main module compatibility shim (src/huey)

"""Expose the maintained :mod:`huey.main` interfaces at the legacy path.

This wrapper keeps imports from ``huey.memory.PY.main`` working while all
runtime behavior remains centralized in ``huey.main``.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

# Reuse the existing, fully featured implementation.
_impl = import_module("huey.main")

app = _impl.app
health_check = _impl.health_check
main = _impl.main
parse_args = _impl.parse_args
readiness_check = _impl.readiness_check
run_setup = _impl.run_setup
version_info = _impl.version_info

__all__ = [
    "app",
    "health_check",
    "main",
    "parse_args",
    "readiness_check",
    "run_setup",
    "version_info",
]


def __getattr__(name: str) -> Any:
    """Delegate attribute access to :mod:`huey.main`."""

    return getattr(_impl, name)


__doc__ = _impl.__doc__
