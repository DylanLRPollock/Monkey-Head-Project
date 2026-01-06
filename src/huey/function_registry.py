# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Function registry compatibility wrapper (src)

"""Expose the shared function registry under :mod:`huey.function_registry`."""

from __future__ import annotations

import sys

from .memory.PY import function_registry as _function_registry

sys.modules[__name__] = _function_registry
