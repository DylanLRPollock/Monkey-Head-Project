# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Battery Hooks module (tests)

from huey.power.management import BatteryMonitor


def test_battery_monitor_events():
    monitor = BatteryMonitor(shutdown_threshold=20.0)
    events: list[tuple[str, float]] = []

    def record(event: str):
        return lambda status: events.append((event, status.get("percent")))

    monitor.register_hook("battery_low", record("low"))
    monitor.register_hook("battery_recovered", record("recovered"))
    monitor.register_hook("power_connected", record("connected"))
    monitor.register_hook("power_disconnected", record("disconnected"))

    monitor.observe({"percent": 18.0, "power_plugged": False})
    monitor.observe({"percent": 25.0, "power_plugged": False})
    monitor.observe({"percent": 30.0, "power_plugged": True})

    assert ("low", 18.0) in events
    assert any(name == "recovered" for name, _ in events)
    assert any(name == "connected" for name, _ in events)
