# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Drivers module (huey/hardware)

"""Built-in sensor and actuator plugins leveraging common robotics libraries."""

from __future__ import annotations

import logging
import random
from typing import Any, Dict, Optional

from .plugins import ActuatorPlugin, ActuatorRegistry, SensorPlugin, SensorRegistry

LOGGER = logging.getLogger(__name__)


class GPIOZeroDigitalSensor(SensorPlugin):
    """Digital GPIO sensor using :mod:`gpiozero`."""

    plugin_name = "gpiozero.digital"

    def setup(self) -> None:
        try:
            from gpiozero import DigitalInputDevice  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "gpiozero is required for GPIOZeroDigitalSensor"
            ) from exc
        pin = int(self.config.get("pin"))
        bounce = float(self.config.get("bounce_time", 0)) or None
        self._device = DigitalInputDevice(pin, bounce_time=bounce)
        LOGGER.debug("Initialised gpiozero sensor %s on pin %s", self.name, pin)

    def read(self) -> Any:
        return float(self._device.value)


class GPIOZeroDigitalActuator(ActuatorPlugin):
    """GPIO actuator using :mod:`gpiozero`."""

    plugin_name = "gpiozero.output"

    def setup(self) -> None:
        try:
            from gpiozero import DigitalOutputDevice  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "gpiozero is required for GPIOZeroDigitalActuator"
            ) from exc
        pin = int(self.config.get("pin"))
        self._device = DigitalOutputDevice(pin)
        LOGGER.debug("Initialised gpiozero actuator %s on pin %s", self.name, pin)

    def perform(self, command: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        device = self._device
        if command == "on":
            device.on()
        elif command == "off":
            device.off()
        elif command == "toggle":
            device.toggle()
        else:
            raise ValueError(f"Unsupported command {command!r} for gpiozero actuator")
        return {"state": command}


class SerialLineSensor(SensorPlugin):
    """Serial sensor using :mod:`pyserial` to read newline terminated data."""

    plugin_name = "serial.line"

    def setup(self) -> None:
        try:
            import serial  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("pyserial is required for SerialLineSensor") from exc
        port = self.config.get("port")
        baudrate = int(self.config.get("baudrate", 9600))
        timeout = float(self.config.get("timeout", 1))
        self._serial = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        LOGGER.debug("Opened serial sensor %s on %s @ %s", self.name, port, baudrate)

    def read(self) -> Any:
        line = self._serial.readline().decode("utf-8", "ignore").strip()
        return line


class SerialCommandActuator(ActuatorPlugin):
    """Serial actuator writing commands using :mod:`pyserial`."""

    plugin_name = "serial.command"

    def setup(self) -> None:
        try:
            import serial  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "pyserial is required for SerialCommandActuator"
            ) from exc
        port = self.config.get("port")
        baudrate = int(self.config.get("baudrate", 9600))
        timeout = float(self.config.get("timeout", 1))
        self._serial = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        LOGGER.debug("Opened serial actuator %s on %s @ %s", self.name, port, baudrate)

    def perform(self, command: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        message = payload.get("message") if payload else command
        data = f"{message}\n".encode("utf-8")
        self._serial.write(data)
        return {"written": message}


class SMBusSensor(SensorPlugin):
    """I2C sensor using :mod:`smbus2`."""

    plugin_name = "i2c.smbus"

    def setup(self) -> None:
        try:
            from smbus2 import SMBus  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("smbus2 is required for SMBusSensor") from exc
        bus_id = int(self.config.get("bus", 1))
        address = int(self.config.get("address"), 0)
        self._bus = SMBus(bus_id)
        self._address = address
        LOGGER.debug(
            "Initialised SMBus sensor %s on bus %s address 0x%X",
            self.name,
            bus_id,
            address,
        )

    def read(self) -> Any:
        register = int(self.config.get("register", 0))
        length = int(self.config.get("length", 2))
        data = self._bus.read_i2c_block_data(self._address, register, length)
        return data


class VirtualRandomSensor(SensorPlugin):
    """Virtual sensor emitting pseudo-random values for development and testing."""

    plugin_name = "virtual.random"

    def read(self) -> Any:
        low = float(self.config.get("low", 0))
        high = float(self.config.get("high", 1))
        precision = int(self.config.get("precision", 3))
        value = random.uniform(low, high)
        return round(value, precision)


def register_builtin_sensors(registry: SensorRegistry) -> None:
    """Register built-in sensor plugins with ``registry``."""

    for plugin in (
        GPIOZeroDigitalSensor,
        SerialLineSensor,
        SMBusSensor,
        VirtualRandomSensor,
    ):
        try:
            registry.register(plugin)
        except Exception:  # pragma: no cover - defensive logging
            LOGGER.exception("Failed to register sensor plugin %s", plugin)


def register_builtin_actuators(registry: ActuatorRegistry) -> None:
    """Register built-in actuator plugins with ``registry``."""

    for plugin in (
        GPIOZeroDigitalActuator,
        SerialCommandActuator,
    ):
        try:
            registry.register(plugin)
        except Exception:  # pragma: no cover - defensive logging
            LOGGER.exception("Failed to register actuator plugin %s", plugin)


__all__ = [
    "GPIOZeroDigitalActuator",
    "GPIOZeroDigitalSensor",
    "SerialCommandActuator",
    "SerialLineSensor",
    "SMBusSensor",
    "VirtualRandomSensor",
    "register_builtin_actuators",
    "register_builtin_sensors",
]
