# Sensor plugin development

HueyOS acquires telemetry via pluggable sensors. Plugins inherit from
`huey.hardware.plugins.SensorPlugin`, implement a `read()` method, and rely on
the `SensorManager` to persist readings into honeycomb storage and broadcast them
to listeners.

## Lifecycle hooks

All plugins inherit from `BasePlugin`, which provides optional `setup()` and
`shutdown()` hooks and exposes provenance metadata shared with API clients.
【F:huey/hardware/plugins.py†L22-L64】 Implement long-running initialisation such
as opening serial devices inside `setup()` and release resources inside
`shutdown()`.

Every call to `capture()` wraps the `read()` output with timestamps and
provenance data, returning a `SensorReading` dataclass.【F:huey/hardware/plugins.py†L32-L55】
`SensorManager.poll_sensor()` invokes `capture()`, stores the payload in the
honeycomb, and fan-outs to live subscribers.【F:huey/hardware/manager.py†L71-L112】

## Minimal plugin example

```python
from huey.hardware.plugins import SensorPlugin

class WorkshopTemperature(SensorPlugin):
    """Reports ambient temperature from an attached microcontroller."""

    plugin_name = "workshop.temperature"

    def setup(self) -> None:
        self.serial_port = open("/dev/ttyUSB0", "rb")

    def read(self) -> float:
        raw = self.serial_port.readline().decode().strip()
        return float(raw)

    def shutdown(self) -> None:
        self.serial_port.close()
```

Register the plugin at runtime using `SensorManager.add_sensor()`:

```python
from huey.hardware.manager import SensorManager

manager = SensorManager()
manager.add_sensor("workshop.temperature", name="shop-temp-1", config={"units": "C"})
```

The manager records each reading under `telemetry/sensor/<name>/<uuid>` inside
the honeycomb store, making it available through `/sensors/*` endpoints and the
history loaders.

## Configuration and provenance

Plugin constructors receive a `config` dictionary. The base class stores it and
exposes it as part of the provenance returned to API consumers.【F:huey/hardware/plugins.py†L24-L47】
Use this channel for calibration constants, units, or thresholds. Since configs
are persisted alongside sensor metadata, operators can audit which parameters
were active when a reading was produced.

## Packaging and entry points

`SensorRegistry` maintains the mapping of symbolic plugin names to classes and
can lazily load additional plugins from the `hueyos.sensors` entry point
group.【F:huey/hardware/plugins.py†L67-L166】 Adding the following to your
`pyproject.toml` registers the example plugin:

```toml
[project.entry-points."hueyos.sensors"]
"workshop.temperature" = "my_package.sensors:WorkshopTemperature"
```

When HueyOS starts it enumerates entry points and makes each plugin visible via
`/sensors/plugins` together with docstrings and sample configuration keys.
Metadata is sourced from `SensorRegistry.describe()` which instantiates the class
and inspects its configuration defaults.【F:huey/hardware/plugins.py†L85-L126】

## Testing plugins

To validate a plugin without hardware, provide a stub implementation that returns
synthetic data—similar to the included `DummyTemperatureSensor`—and register it
during development or unit tests.【F:huey/hardware/plugins.py†L167-L198】 Use the
`sensor_manager` streaming helpers to assert that readings propagate to
subscribers and appear in honeycomb history queries.
