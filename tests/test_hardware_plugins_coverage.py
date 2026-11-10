"""Coverage for sensor and actuator plugin registry contracts."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from huey.hardware import plugins
from huey.hardware.plugins import (
    ActuatorPlugin,
    ActuatorRegistry,
    DummyTemperatureSensor,
    SensorPlugin,
    SensorRegistry,
    import_from_string,
    list_sensor_plugin_metadata,
    list_sensor_plugins,
    load_plugins_from_definitions,
)


class ReadingSensor(SensorPlugin):
    """Example sensor plugin used by registry tests."""

    plugin_name = "test.reading"

    def read(self):
        return self.config.get("value", 4)


class InvalidClass:
    pass


class DemoActuator(ActuatorPlugin):
    plugin_name = "test.actuator"

    def perform(self, command, payload=None):
        return command, payload


def test_registry_register_create_describe_and_list_helpers():
    registry = SensorRegistry()
    registry.register(ReadingSensor)

    instance = registry.create("test.reading", "one", {"value": 9})
    description = registry.describe("test.reading")

    assert instance.capture().value == 9
    assert description["plugin"] == "test.reading"
    assert description["description"] == "Example sensor plugin used by registry tests."
    assert description["config_keys"] == []
    assert registry.available() == ["test.reading"]
    assert [item["name"] for item in registry.describe_all()] == ["test.reading"]
    assert list_sensor_plugins(registry) == ["test.reading"]
    assert list_sensor_plugin_metadata(registry)[0]["name"] == "test.reading"
    with pytest.raises(KeyError, match="Unknown sensor plugin"):
        registry.get("absent")


def test_registry_describe_reports_sample_config_keys():
    class ConfiguredSensor(ReadingSensor):
        plugin_name = "configured"

        def __init__(self, name, config=None):
            super().__init__(name, config or {"port": 7})

    registry = SensorRegistry()
    registry.register(ConfiguredSensor)
    assert registry.describe("configured")["config_keys"] == ["port"]


def test_entry_point_select_loads_sensor_plugin_once(monkeypatch):
    calls = []
    entry = SimpleNamespace(load=lambda: calls.append("loaded") or ReadingSensor)

    class EntryPoints:
        def select(self, *, group):
            calls.append(group)
            return [entry] if group == "huey.os.sensors" else []

    monkeypatch.setattr(
        plugins.importlib_metadata, "entry_points", lambda: EntryPoints()
    )
    registry = SensorRegistry()

    assert registry.available() == ["test.reading"]
    assert registry.get("test.reading") is ReadingSensor
    assert calls == ["huey.os.sensors", "loaded"]


def test_entry_point_falls_back_to_legacy_group(monkeypatch):
    entry = SimpleNamespace(load=lambda: ReadingSensor)

    class EntryPoints:
        def select(self, *, group):
            return [entry] if group == "hueyos.sensors" else []

    monkeypatch.setattr(
        plugins.importlib_metadata, "entry_points", lambda: EntryPoints()
    )
    assert SensorRegistry().available() == ["test.reading"]


def test_entry_point_supports_mapping_api(monkeypatch):
    entry = SimpleNamespace(load=lambda: ReadingSensor)
    monkeypatch.setattr(
        plugins.importlib_metadata,
        "entry_points",
        lambda: {"huey.os.sensors": [entry], "hueyos.sensors": []},
    )
    assert SensorRegistry().available() == ["test.reading"]


def test_entry_point_loader_ignores_non_class_and_wrong_base(monkeypatch, caplog):
    entries = [
        SimpleNamespace(load=lambda: "not a class"),
        SimpleNamespace(load=lambda: InvalidClass),
    ]

    class EntryPoints:
        def select(self, *, group):
            return entries if group == "huey.os.sensors" else []

    monkeypatch.setattr(
        plugins.importlib_metadata, "entry_points", lambda: EntryPoints()
    )
    assert SensorRegistry().available() == []
    assert "did not return a class" in caplog.text
    assert "does not implement SensorPlugin" in caplog.text


def test_import_from_string_accepts_colon_and_dot_paths_and_validates_type():
    assert (
        import_from_string("huey.hardware.plugins:DummyTemperatureSensor")
        is DummyTemperatureSensor
    )
    assert (
        import_from_string("huey.hardware.plugins.DummyTemperatureSensor")
        is DummyTemperatureSensor
    )
    with pytest.raises(TypeError, match="not a SensorPlugin"):
        import_from_string("huey.hardware.plugins:ActuatorPlugin")


def test_load_plugins_uses_registry_then_import_path_fallback():
    registry = SensorRegistry()
    registry.register(ReadingSensor)
    instances = load_plugins_from_definitions(
        [
            ("test.reading", "registered", {"value": 5}),
            (
                "huey.hardware.plugins:DummyTemperatureSensor",
                "dynamic",
                {"baseline": 18},
            ),
        ],
        registry,
    )

    assert [sensor.name for sensor in instances] == ["registered", "dynamic"]
    assert instances[0].capture().value == 5
    assert instances[1].capture().value == 18


def test_dummy_sensor_defaults_and_actuator_registry_contract():
    sensor = DummyTemperatureSensor("room")
    assert sensor.capture().value == 21.0

    registry = ActuatorRegistry()
    registry.register(DemoActuator)
    assert registry.available() == ["test.actuator"]
    assert registry.create("test.actuator", "lamp").perform("on", {"level": 2}) == (
        "on",
        {"level": 2},
    )
    with pytest.raises(KeyError, match="Unknown actuator plugin"):
        registry.get("missing")


def test_registries_replace_duplicate_names_and_reject_empty_plugin_classes(caplog):
    caplog.set_level("DEBUG")
    registry = SensorRegistry()
    registry.register(ReadingSensor)
    registry.register(ReadingSensor)
    assert "Replacing existing sensor plugin" in caplog.text

    empty_sensor = type(
        "", (SensorPlugin,), {"plugin_name": "", "read": lambda _self: 0}
    )
    with pytest.raises(ValueError, match="Sensor plugins must define"):
        registry.register(empty_sensor)

    empty_actuator = type(
        "",
        (ActuatorPlugin,),
        {"plugin_name": "", "perform": lambda _self, _command, _payload=None: None},
    )
    with pytest.raises(ValueError, match="Actuator plugins must define"):
        ActuatorRegistry().register(empty_actuator)
