# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: PyGPT custom CLI compatibility wrapper (src)

"""Expose the maintained CustomPyGPT implementation under :mod:`huey`.

This wrapper keeps legacy imports stable while routing to the richer
implementation in :mod:`huey.memory.PY.pygpt_custom_cli`.
"""

from __future__ import annotations

from .memory.PY import pygpt_custom_cli as _pygpt_custom_cli

__all__ = list(getattr(_pygpt_custom_cli, "__all__", ()))

globals().update({name: getattr(_pygpt_custom_cli, name) for name in __all__})
