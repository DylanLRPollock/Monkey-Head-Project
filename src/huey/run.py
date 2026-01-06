# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Run compatibility wrapper (src)

"""Expose legacy runtime entry points under :mod:`huey.run`."""

from __future__ import annotations

import sys

from .memory.PY import run as _run

sys.modules[__name__] = _run
