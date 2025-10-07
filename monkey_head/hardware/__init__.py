"""Hardware integration layer for HueyOS.

This package provides abstractions around sensors and actuators along with
managers that coordinate data collection, storage, and runtime telemetry
streaming.  It is intentionally lightweight so that downstream projects can
extend the robotics stack without touching core application code.
"""

from .manager import (
    ActuatorManager,
    SensorManager,
    create_default_actuator_manager,
    create_default_sensor_manager,
)
from .plugins import ActuatorPlugin, ActuatorRegistry, SensorPlugin, SensorReading, SensorRegistry

__all__ = [
    "ActuatorManager",
    "ActuatorPlugin",
    "ActuatorRegistry",
    "SensorManager",
    "create_default_actuator_manager",
    "SensorPlugin",
    "SensorReading",
    "SensorRegistry",
    "create_default_sensor_manager",
]

