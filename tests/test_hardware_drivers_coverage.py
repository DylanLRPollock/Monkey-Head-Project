"""Exercise hardware drivers with simulated devices and no physical I/O."""

from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from huey.hardware import drivers
from huey.hardware.plugins import ActuatorRegistry, SensorRegistry


class FakeDigitalInput:
    def __init__(self, pin, *, bounce_time):
        self.pin = pin
        self.bounce_time = bounce_time
        self.value = True


class FakeDigitalOutput:
    def __init__(self, pin):
        self.pin = pin
        self.events = []

    def on(self):
        self.events.append("on")

    def off(self):
        self.events.append("off")

    def toggle(self):
        self.events.append("toggle")


class FakeSerial:
    def __init__(self, port, *, baudrate, timeout):
        self.settings = (port, baudrate, timeout)
        self.writes = []

    def readline(self):
        return b"  ready\xff\n"

    def write(self, data):
        self.writes.append(data)


class FakeSMBus:
    def __init__(self, bus_id):
        self.bus_id = bus_id
        self.requests = []

    def read_i2c_block_data(self, address, register, length):
        self.requests.append((address, register, length))
        return [1, 2, 3]


def test_gpio_sensor_and_actuator_use_configured_pins(monkeypatch):
    monkeypatch.setitem(
        sys.modules,
        "gpiozero",
        SimpleNamespace(
            DigitalInputDevice=FakeDigitalInput,
            DigitalOutputDevice=FakeDigitalOutput,
        ),
    )
    sensor = drivers.GPIOZeroDigitalSensor("door", {"pin": "17", "bounce_time": 0.2})
    sensor.setup()
    assert sensor.read() == 1.0
    assert sensor._device.pin == 17
    assert sensor._device.bounce_time == 0.2

    actuator = drivers.GPIOZeroDigitalActuator("lamp", {"pin": 22})
    actuator.setup()
    assert actuator.perform("on") == {"state": "on"}
    assert actuator.perform("off") == {"state": "off"}
    assert actuator.perform("toggle") == {"state": "toggle"}
    assert actuator._device.events == ["on", "off", "toggle"]
    with pytest.raises(ValueError, match="Unsupported command"):
        actuator.perform("dim")


def test_gpio_sensor_zero_bounce_is_normalized_to_none(monkeypatch):
    monkeypatch.setitem(
        sys.modules,
        "gpiozero",
        SimpleNamespace(DigitalInputDevice=FakeDigitalInput),
    )
    sensor = drivers.GPIOZeroDigitalSensor("door", {"pin": 3})
    sensor.setup()
    assert sensor._device.bounce_time is None


def test_serial_sensor_decodes_and_strips_lines(monkeypatch):
    monkeypatch.setitem(sys.modules, "serial", SimpleNamespace(Serial=FakeSerial))
    sensor = drivers.SerialLineSensor(
        "console", {"port": "/dev/fake", "baudrate": "19200", "timeout": "0.5"}
    )
    sensor.setup()
    assert sensor.read() == "ready"
    assert sensor._serial.settings == ("/dev/fake", 19200, 0.5)


def test_serial_actuator_uses_payload_message_or_command(monkeypatch):
    monkeypatch.setitem(sys.modules, "serial", SimpleNamespace(Serial=FakeSerial))
    actuator = drivers.SerialCommandActuator("console", {"port": "/dev/fake"})
    actuator.setup()
    assert actuator.perform("status") == {"written": "status"}
    assert actuator.perform("say", {"message": "hello"}) == {"written": "hello"}
    assert actuator._serial.writes == [b"status\n", b"hello\n"]


def test_smbus_sensor_reads_configured_register_block(monkeypatch):
    monkeypatch.setitem(sys.modules, "smbus2", SimpleNamespace(SMBus=FakeSMBus))
    sensor = drivers.SMBusSensor(
        "imu", {"bus": "2", "address": "0x68", "register": "3", "length": "6"}
    )
    sensor.setup()
    assert sensor.read() == [1, 2, 3]
    assert sensor._bus.bus_id == 2
    assert sensor._bus.requests == [(0x68, 3, 6)]


def test_virtual_random_sensor_applies_bounds_and_precision(monkeypatch):
    monkeypatch.setattr(drivers.random, "uniform", lambda low, high: (low + high) / 2)
    sensor = drivers.VirtualRandomSensor(
        "virtual", {"low": "2", "high": "4", "precision": "1"}
    )
    assert sensor.read() == 3.0


def test_builtin_registration_lists_all_supported_plugins():
    sensors = SensorRegistry()
    actuators = ActuatorRegistry()

    drivers.register_builtin_sensors(sensors)
    drivers.register_builtin_actuators(actuators)

    assert sensors.available() == [
        "gpiozero.digital",
        "i2c.smbus",
        "serial.line",
        "virtual.random",
    ]
    assert actuators.available() == ["gpiozero.output", "serial.command"]
