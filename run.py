# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Run module

"""Convenience proxy to expose the Huey runtime entry points at the project root."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent
_SRC_PATH = _PROJECT_ROOT / "src"
if str(_SRC_PATH) not in sys.path:
    sys.path.insert(0, str(_SRC_PATH))

_module = importlib.import_module("huey.run")

__all__ = getattr(_module, "__all__", [])
globals().update({name: getattr(_module, name) for name in __all__})
