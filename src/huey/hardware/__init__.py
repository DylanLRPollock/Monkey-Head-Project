# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Package initializer for huey/hardware

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
from .actuators import ActuatorHub
from .cooling import CoolingController
from .gpio import GPIOController
from .legacy import LegacyHardwareBridge
from .motherboard import MotherboardProfile
from .optane import OptaneManager
from .power import PowerController
from .sensors import SensorHub
from .serial import SerialBus
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

__all__ = [
    "ActuatorManager",
    "ActuatorHub",
    "ActuatorPlugin",
    "ActuatorRegistry",
    "CoolingController",
    "DummyTemperatureSensor",
    "GPIOController",
    "LegacyHardwareBridge",
    "MotherboardProfile",
    "OptaneManager",
    "PowerController",
    "SensorManager",
    "SensorHub",
    "create_default_actuator_manager",
    "SensorPlugin",
    "SensorReading",
    "SensorRegistry",
    "SerialBus",
    "list_sensor_plugin_metadata",
    "list_sensor_plugins",
    "create_default_sensor_manager",
]
