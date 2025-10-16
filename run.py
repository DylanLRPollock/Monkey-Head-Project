# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Run module

"""Convenience proxy to expose the Huey runtime entry points at the project root."""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent
_SRC_PATH = _PROJECT_ROOT / "src"
for path in (str(_PROJECT_ROOT), str(_SRC_PATH)):
    if path not in sys.path:
        sys.path.insert(0, path)

_MODULE_PATH = _PROJECT_ROOT / "huey" / "run.py"
_SPEC = importlib.util.spec_from_file_location("huey.run", _MODULE_PATH)
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover - invalid spec
    raise ImportError(f"Cannot load huey.run from {_MODULE_PATH}")

_module = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_module)
sys.modules.setdefault("huey.run", _module)

__all__ = getattr(_module, "__all__", [])
globals().update({name: getattr(_module, name) for name in __all__})
