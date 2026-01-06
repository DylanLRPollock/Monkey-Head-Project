# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Exceptions compatibility wrapper (src)

"""Expose shared exception types under :mod:`huey.exceptions`."""

from __future__ import annotations

from .memory.PY.exceptions import (  # noqa: F401
    DataNotFoundError,
    HueyError,
    InvalidInputError,
)

__all__ = [
    "HueyError",
    "DataNotFoundError",
    "InvalidInputError",
]
