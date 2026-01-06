# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: PDF utils compatibility wrapper (src)

"""Expose PDF helpers under :mod:`huey.pdf_utils`."""

from __future__ import annotations

import sys

from .memory.PY import pdf_utils as _pdf_utils

sys.modules[__name__] = _pdf_utils
