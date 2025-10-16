# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Package initializer for src/monkey_head/hardware

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
    DummyTemperatureSensor,
    SensorPlugin,
    SensorReading,
    SensorRegistry,
    list_sensor_plugin_metadata,
    list_sensor_plugins,
)

_drivers = import_module("huey.hardware.drivers")

drivers = _drivers

__all__ = [
    "ActuatorManager",
    "ActuatorPlugin",
    "ActuatorRegistry",
    "DummyTemperatureSensor",
    "SensorManager",
    "SensorPlugin",
    "SensorReading",
    "SensorRegistry",
    "create_default_actuator_manager",
    "create_default_sensor_manager",
    "list_sensor_plugin_metadata",
    "list_sensor_plugins",
    "drivers",
]
