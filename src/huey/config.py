# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Config compatibility wrapper (src)

"""Expose configuration helpers under :mod:`huey.config`."""

from __future__ import annotations

from .memory.PY.config import load_config

__all__ = ["load_config"]
