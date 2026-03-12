# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Hardware Manager module (tests)

import logging

from huey.hardware.manager import SensorManager
from huey.hardware.plugins import SensorPlugin, SensorRegistry
from huey.honeycomb.storage import HoneycombStorage


class _DemoSensor(SensorPlugin):
    plugin_name = "demo\r\nplugin"

    def read(self) -> float:
        return 1.0


def test_sensor_manager_logs_strip_control_characters(tmp_path, caplog):
    storage = HoneycombStorage(base_dir=tmp_path)
    registry = SensorRegistry()
    registry.register(_DemoSensor)
    manager = SensorManager(storage=storage, registry=registry)

    with caplog.at_level(logging.INFO, logger="huey.hardware.manager"):
        manager.add_sensor("demo\r\nplugin", "sensor\r\nname")
        manager.register_instance(_DemoSensor(name="inline\r\nsensor"))
        manager.remove_sensor("sensor\r\nname")

    messages = [record.getMessage() for record in caplog.records]
    assert messages
    assert all("\r" not in message and "\n" not in message for message in messages)
