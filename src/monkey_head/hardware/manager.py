# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Manager module (src/monkey_head/hardware)

"""Compatibility wrapper for :mod:`huey.hardware.manager`."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

_impl = import_module("huey.hardware.manager")

__all__ = list(getattr(_impl, "__all__", ()))
if not __all__:
    __all__ = [
        "ActuatorManager",
        "SensorManager",
        "create_default_actuator_manager",
        "create_default_sensor_manager",
    ]

for name in __all__:
    globals()[name] = getattr(_impl, name)


def __getattr__(name: str) -> Any:
    return getattr(_impl, name)


__doc__ = _impl.__doc__


if TYPE_CHECKING:  # pragma: no cover - import for type checkers only
    from huey.hardware.manager import (
        ActuatorManager,
        SensorManager,
        create_default_actuator_manager,
        create_default_sensor_manager,
    )
