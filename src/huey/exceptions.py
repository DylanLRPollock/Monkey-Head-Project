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


class RuntimeConfigurationError(HueyError):
    """Raised when the runtime configuration is invalid or incomplete."""


class KernelBootError(HueyError):
    """Raised when the GenCore boot sequence cannot complete."""


class KernelModuleError(HueyError):
    """Raised when a kernel module cannot be registered or activated."""


class StorageError(HueyError):
    """Raised when honeycomb storage operations fail."""


class GovernanceError(HueyError):
    """Raised when governance policies reject an action."""


class HardwareError(HueyError):
    """Raised when hardware orchestration fails."""


class NetworkError(HueyError):
    """Raised when network orchestration fails."""

__all__ = [
    "HueyError",
    "DataNotFoundError",
    "InvalidInputError",
    "GovernanceError",
    "HardwareError",
    "KernelBootError",
    "KernelModuleError",
    "NetworkError",
    "RuntimeConfigurationError",
    "StorageError",
]
