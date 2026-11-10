"""Focused lifecycle, telemetry, streaming, and registry manager tests."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest

from huey.hardware import drivers as hardware_drivers
from huey.hardware.manager import (
    ActuatorManager,
    SensorManager,
    create_default_actuator_manager,
    create_default_sensor_manager,
)
from huey.hardware.plugins import (
    ActuatorPlugin,
    ActuatorRegistry,
    SensorPlugin,
    SensorReading,
    SensorRegistry,
)


class MemoryStorage:
    def __init__(self):
        self.records = {}

    def store(self, key, data):
        self.records[key] = Record(data.copy())

    def list_keys(self, prefix=None):
        keys = list(self.records)
        return [key for key in keys if prefix is None or key.startswith(prefix)]

    def get_record(self, key):
        return self.records.get(key)


@dataclass
class Record:
    data: dict


class DemoSensor(SensorPlugin):
    plugin_name = "demo"

    def setup(self):
        self.config.setdefault("setup", True)

    def read(self):
        return self.config.get("value", 7)


class BrokenSensor(DemoSensor):
    plugin_name = "broken"

    def read(self):
        raise RuntimeError("sensor failed")

    def shutdown(self):
        raise RuntimeError("shutdown failed")


class DemoActuator(ActuatorPlugin):
    plugin_name = "lamp"

    def perform(self, command, payload=None):
        return command, payload


class BrokenShutdownActuator(DemoActuator):
    def shutdown(self):
        raise RuntimeError("shutdown failed")


class Telemetry:
    def __init__(self, error=None):
        self.readings = []
        self.error = error

    def log_sensor_reading(self, reading):
        if self.error:
            raise self.error
        self.readings.append(reading)


def make_sensor_manager(telemetry_store=None):
    registry = SensorRegistry()
    registry.register(DemoSensor)
    registry.register(BrokenSensor)
    storage = MemoryStorage()
    manager = SensorManager(
        storage=storage, registry=registry, telemetry_store=telemetry_store
    )
    return manager, storage


def test_sensor_lifecycle_bulk_registration_and_metadata_are_independent():
    manager, _ = make_sensor_manager()
    definitions = [("demo", "temperature", {"value": 22})]
    sensors = manager.add_plugins(definitions)
    assert sensors[0].config["setup"] is True
    sensors[0].config["value"] = 23

    listed = manager.list_sensors()
    assert listed[0]["name"] == "temperature"
    assert listed[0]["config"] == {"value": 23, "setup": True}
    assert manager.get_sensor("temperature") is sensors[0]
    assert manager.get_sensor("missing") is None

    manager.remove_sensor("temperature")
    manager.remove_sensor("temperature")
    assert manager.list_sensors() == []


def test_sensor_capture_records_payload_and_broadcasts_to_matching_subscribers():
    telemetry = Telemetry()
    manager, storage = make_sensor_manager(telemetry)
    manager.add_sensor("demo", "temperature", {"value": 19})
    matching = manager.subscribe("temperature")
    other = manager.subscribe("humidity")
    everyone = manager.subscribe()

    reading = manager.poll_sensor("temperature")

    assert reading.value == 19
    assert matching.get_nowait() is reading
    assert everyone.get_nowait() is reading
    assert other.empty()
    assert telemetry.readings == [reading]
    (key,) = storage.list_keys("telemetry/sensor/temperature/")
    assert storage.get_record(key).data == {
        "name": "temperature",
        "value": 19,
        "timestamp": reading.timestamp,
        "provenance": reading.provenance,
    }
    with pytest.raises(KeyError, match="Unknown sensor absent"):
        manager.poll_sensor("absent")


def test_poll_all_skips_failed_sensor_and_telemetry_errors_are_isolated(caplog):
    manager, _ = make_sensor_manager(Telemetry(error=RuntimeError("telemetry down")))
    manager.add_sensor("demo", "working")
    manager.add_sensor("broken", "failing")

    readings = manager.poll_all()

    assert [reading.name for reading in readings] == ["working"]
    assert "failed to capture reading" in caplog.text
    assert "Failed to persist sensor reading" in caplog.text


def test_register_instance_and_remove_suppress_plugin_shutdown_errors():
    manager, _ = make_sensor_manager()
    sensor = BrokenSensor("prebuilt")
    manager.register_instance(sensor)
    assert manager.get_sensor("prebuilt") is sensor
    manager.remove_sensor("prebuilt")
    assert manager.get_sensor("prebuilt") is None


def test_unsubscribe_removes_only_the_requested_queue():
    manager, _ = make_sensor_manager()
    first = manager.subscribe()
    second = manager.subscribe()

    manager.unsubscribe(first)
    manager._broadcast(SensorReading("ambient", 1, 2.0))

    assert first.empty()
    assert second.qsize() == 1


def test_async_stream_unsubscribes_when_closed():
    async def exercise_stream():
        manager, _ = make_sensor_manager()
        stream = manager.stream("temperature")
        pending = asyncio.create_task(anext(stream))
        await asyncio.sleep(0)
        manager._broadcast(SensorReading("temperature", 25, 3.0))
        reading = await pending
        assert reading.value == 25
        await stream.aclose()
        assert manager._subscribers == []

    asyncio.run(exercise_stream())


def test_history_applies_limit_adds_key_and_sorts_by_timestamp():
    manager, storage = make_sensor_manager()
    for suffix, timestamp in (("a", 3), ("b", 1), ("c", 2)):
        storage.store(
            f"telemetry/sensor/temperature/{suffix}",
            {"name": "temperature", "timestamp": timestamp},
        )

    history = manager.load_history("temperature", limit=2)
    assert [item["timestamp"] for item in history] == [1, 2]
    assert history[0]["key"].endswith("/b")
    storage.records["telemetry/sensor/temperature/missing"] = None
    assert len(manager.load_history("temperature", limit=0)) == 3


def test_actuator_manager_lifecycle_listing_perform_and_missing_names():
    registry = ActuatorRegistry()
    registry.register(DemoActuator)
    manager = ActuatorManager(registry=registry)
    actuator = manager.add_actuator("lamp", "desk")

    assert manager.list_actuators()[0]["name"] == "desk"
    assert manager.perform("desk", "on", {"level": 3}) == ("on", {"level": 3})
    manager.register_instance(BrokenShutdownActuator("hall"))
    assert {item["name"] for item in manager.list_actuators()} == {"desk", "hall"}
    manager.remove_actuator("hall")
    manager.remove_actuator("missing")
    with pytest.raises(KeyError, match="Unknown actuator missing"):
        manager.perform("missing", "on")
    assert manager.perform("desk", "off") == ("off", None)
    manager.remove_actuator("desk")
    assert manager.list_actuators() == []
    assert actuator.name == "desk"


def test_default_manager_factories_register_builtin_plugins(monkeypatch):
    registered = []

    class Drivers:
        @staticmethod
        def register_builtin_sensors(registry):
            registered.append("sensors")
            registry.register(DemoSensor)

        @staticmethod
        def register_builtin_actuators(registry):
            registered.append("actuators")
            registry.register(DemoActuator)

    monkeypatch.setattr(
        hardware_drivers, "register_builtin_sensors", Drivers.register_builtin_sensors
    )
    monkeypatch.setattr(
        hardware_drivers,
        "register_builtin_actuators",
        Drivers.register_builtin_actuators,
    )
    sensor_manager = create_default_sensor_manager()
    actuator_manager = create_default_actuator_manager()

    assert sensor_manager.registry.available() == ["demo"]
    assert actuator_manager.registry.available() == ["lamp"]
    assert registered == ["sensors", "actuators"]


def test_sensor_poll_without_telemetry_store_only_persists_to_storage():
    manager, storage = make_sensor_manager()
    manager.add_sensor("demo", "temperature")

    reading = manager.poll_sensor("temperature")

    assert len(storage.list_keys("telemetry/sensor/temperature/")) == 1
    assert reading.value == 7
