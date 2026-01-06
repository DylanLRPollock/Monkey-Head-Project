# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: API compatibility wrapper (src)

"""Expose the FastAPI application under :mod:`huey.api`."""

from __future__ import annotations

import sys

from .memory.PY import api as _api

sys.modules[__name__] = _api
