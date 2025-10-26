# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Resilience module (src/monkey_head/core)

"""Compatibility wrapper for :mod:`huey.core.resilience`."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

_impl = import_module("huey.core.resilience")

__all__ = list(getattr(_impl, "__all__", ()))
if not __all__:
    __all__ = [
        "CrashEvent",
        "CrashRecoveryManager",
        "EmergencyGovernanceController",
        "EmergencyServiceStatus",
        "EmergencyState",
        "HealthCheck",
        "MonitoredProcess",
        "RestartCallback",
        "SystemdWatchdogClient",
    ]

for name in __all__:
    globals()[name] = getattr(_impl, name)


def __getattr__(name: str) -> Any:
    return getattr(_impl, name)


__doc__ = _impl.__doc__


if TYPE_CHECKING:  # pragma: no cover - import for type checkers only
    from huey.core.resilience import (
        CrashEvent,
        CrashRecoveryManager,
        EmergencyGovernanceController,
        EmergencyServiceStatus,
        EmergencyState,
        HealthCheck,
        MonitoredProcess,
        RestartCallback,
        SystemdWatchdogClient,
    )
