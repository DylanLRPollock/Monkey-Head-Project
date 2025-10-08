"""Compatibility package for hardware integrations."""

from __future__ import annotations

from importlib import import_module

from .manager import (
    ActuatorManager,
    SensorManager,
    create_default_actuator_manager,
    create_default_sensor_manager,
)
from .plugins import (
    ActuatorPlugin,
    ActuatorRegistry,
    SensorPlugin,
    SensorReading,
    SensorRegistry,
)

_drivers = import_module("huey.hardware.drivers")

drivers = _drivers

__all__ = [
    "ActuatorManager",
    "ActuatorPlugin",
    "ActuatorRegistry",
    "SensorManager",
    "SensorPlugin",
    "SensorReading",
    "SensorRegistry",
    "create_default_actuator_manager",
    "create_default_sensor_manager",
    "drivers",
]
