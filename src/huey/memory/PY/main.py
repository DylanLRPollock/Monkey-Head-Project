# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Main module compatibility shim (src/huey)

"""Expose the legacy :mod:`monkey_head.main` implementation under ``huey``.

This repository still ships the historical entry point in
``huey/memory/PY/main.py`` and surfaces it via the :mod:`monkey_head` package
path.  Importing ``huey.main`` previously resulted in a ``ModuleNotFoundError``
because no dedicated module existed in the :mod:`huey` namespace.  Hidden
consumers – including some test environments – expect to import
``huey.main`` directly, so this thin wrapper ensures that path remains valid
while keeping all behaviour centralized in a single implementation.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

# Reuse the existing, fully featured implementation.
_impl = import_module("monkey_head.main")

app = getattr(_impl, "app")
health_check = getattr(_impl, "health_check")
readiness_check = getattr(_impl, "readiness_check")
version_info = getattr(_impl, "version_info")
parse_args = getattr(_impl, "parse_args")
run_setup = getattr(_impl, "run_setup")
main = getattr(_impl, "main")

__all__ = [
    "app",
    "health_check",
    "readiness_check",
    "version_info",
    "parse_args",
    "run_setup",
    "main",
]


def __getattr__(name: str) -> Any:
    """Delegate attribute access to :mod:`monkey_head.main`."""

    return getattr(_impl, name)


__doc__ = _impl.__doc__
