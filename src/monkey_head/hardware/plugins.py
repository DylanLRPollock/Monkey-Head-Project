# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Plugins module (src/monkey_head/hardware)

"""Compatibility wrapper for :mod:`huey.hardware.plugins`."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_impl = import_module("huey.hardware.plugins")

__all__ = list(getattr(_impl, "__all__", ()))
if not __all__:
    __all__ = [
        "ActuatorPlugin",
        "ActuatorRegistry",
        "SensorPlugin",
        "SensorReading",
        "SensorRegistry",
        "load_plugins_from_definitions",
    ]

for name in __all__:
    globals()[name] = getattr(_impl, name)


def __getattr__(name: str) -> Any:
    return getattr(_impl, name)


__doc__ = _impl.__doc__
