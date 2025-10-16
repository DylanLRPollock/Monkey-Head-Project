# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Plugins module (huey/hardware)

"""Plugin infrastructure for HueyOS hardware integrations."""

from __future__ import annotations

import importlib
import inspect
import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple, Type

try:  # pragma: no cover - importlib.metadata name differs pre-3.10
    from importlib import metadata as importlib_metadata
except ImportError:  # pragma: no cover - fallback for very old Python
    import importlib_metadata  # type: ignore


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class SensorReading:
    """Single sensor reading captured by :class:`SensorManager`."""

    name: str
    value: Any
    timestamp: float
    provenance: Dict[str, Any] = field(default_factory=dict)


class BasePlugin(ABC):
    """Common functionality shared between sensors and actuators."""

    plugin_name: str = ""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None) -> None:
        self.name = name
        self.config = config.copy() if config else {}
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------
    def setup(self) -> None:
        """Initialise the plugin.

        Subclasses may override this method to perform expensive operations
        (e.g., opening serial ports).  The default implementation does nothing.
        """

    def shutdown(self) -> None:
        """Release any resources allocated during :meth:`setup`."""

    # ------------------------------------------------------------------
    # Provenance information
    # ------------------------------------------------------------------
    @property
    def provenance(self) -> Dict[str, Any]:
        """Metadata describing the plugin implementation."""

        return {
            "plugin": self.plugin_name or self.__class__.__name__,
            "module": f"{self.__class__.__module__}.{self.__class__.__qualname__}",
            "config": self.config,
        }


class SensorPlugin(BasePlugin):
    """Base class for sensor plugins."""

    @abstractmethod
    def read(self) -> Any:
        """Collect a reading from the sensor."""

    def capture(self) -> SensorReading:
        """Return a :class:`SensorReading` enriched with provenance data."""

        with self._lock:
            value = self.read()
        return SensorReading(
            name=self.name,
            value=value,
            timestamp=time.time(),
            provenance=self.provenance,
        )


class ActuatorPlugin(BasePlugin):
    """Base class for actuator plugins."""

    @abstractmethod
    def perform(self, command: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a command against the actuator."""


class SensorRegistry:
    """Registry and plugin loader for sensors."""

    def __init__(self) -> None:
        self._plugins: Dict[str, Type[SensorPlugin]] = {}
        self._loaded_entry_points = False

    # ------------------------------------------------------------------
    def register(self, plugin: Type[SensorPlugin]) -> None:
        """Register ``plugin`` under its :attr:`SensorPlugin.plugin_name`."""

        name = getattr(plugin, "plugin_name", None) or plugin.__name__
        if not name:
            raise ValueError("Sensor plugins must define plugin_name")
        if name in self._plugins:
            LOGGER.debug("Replacing existing sensor plugin for name %s", name)
        self._plugins[name] = plugin

    # ------------------------------------------------------------------
    def get(self, name: str) -> Type[SensorPlugin]:
        """Return the plugin class registered as ``name``."""

        self._ensure_entry_points_loaded()
        if name not in self._plugins:
            raise KeyError(f"Unknown sensor plugin: {name}")
        return self._plugins[name]

    # ------------------------------------------------------------------
    def available(self) -> List[str]:
        """Return a sorted list of registered sensor plugin names."""

        self._ensure_entry_points_loaded()
        return sorted(self._plugins)

    # ------------------------------------------------------------------
    def describe(self, name: str) -> Dict[str, Any]:
        """Return metadata describing the plugin registered as ``name``."""

        plugin_cls = self.get(name)
        description = inspect.cleandoc(plugin_cls.__doc__ or "")
        config_keys: List[str] = []
        try:
            sample = plugin_cls(name="__describe__")
        except Exception:  # pragma: no cover - plugin misbehaviour
            LOGGER.debug("Failed to instantiate sensor plugin %s for metadata", name, exc_info=True)
        else:
            config_keys = sorted(sample.config.keys())
            del sample
        return {
            "name": name,
            "module": f"{plugin_cls.__module__}.{plugin_cls.__qualname__}",
            "description": description,
            "plugin": getattr(plugin_cls, "plugin_name", name),
            "config_keys": config_keys,
        }

    # ------------------------------------------------------------------
    def describe_all(self) -> List[Dict[str, Any]]:
        """Return metadata for every registered plugin."""

        self._ensure_entry_points_loaded()
        metadata = []
        for name in self.available():
            try:
                metadata.append(self.describe(name))
            except Exception:  # pragma: no cover - defensive logging
                LOGGER.exception("Failed to describe sensor plugin %s", name)
        return metadata

    # ------------------------------------------------------------------
    def create(self, plugin_name: str, name: str, config: Optional[Dict[str, Any]] = None) -> SensorPlugin:
        """Instantiate a sensor plugin by symbolic ``plugin_name``."""

        plugin_cls = self.get(plugin_name)
        return plugin_cls(name=name, config=config)

    # ------------------------------------------------------------------
    def _ensure_entry_points_loaded(self) -> None:
        if self._loaded_entry_points:
            return
        self._loaded_entry_points = True
        try:
            entry_points = importlib_metadata.entry_points()
        except Exception:  # pragma: no cover - defensive fallback
            LOGGER.exception("Unable to enumerate sensor entry points")
            return
        groups = getattr(entry_points, "select", None)
        if callable(groups):
            sensors = groups(group="monkey_head.sensors")
        else:  # pragma: no cover - importlib_metadata < 3.10 compatibility
            sensors = entry_points.get("monkey_head.sensors", [])  # type: ignore[assignment]
        for entry_point in sensors:
            try:
                plugin_cls = entry_point.load()
            except Exception:  # pragma: no cover - plugin misbehaviour
                LOGGER.exception("Failed to load sensor plugin from %s", entry_point)
                continue
            if not isinstance(plugin_cls, type):
                LOGGER.warning(
                    "Entry point %s did not return a class (got %r)", entry_point, plugin_cls
                )
                continue
            if not issubclass(plugin_cls, SensorPlugin):
                LOGGER.warning(
                    "Entry point %s does not implement SensorPlugin", entry_point
                )
                continue
            self.register(plugin_cls)


def import_from_string(path: str) -> Type[SensorPlugin]:
    """Import a class defined by ``path`` (``package.module:Class``)."""

    if ":" in path:
        module_path, cls_name = path.split(":", 1)
    else:
        module_path, cls_name = path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    cls = getattr(module, cls_name)
    if not isinstance(cls, type) or not issubclass(cls, SensorPlugin):
        raise TypeError(f"{path} is not a SensorPlugin subclass")
    return cls


def load_plugins_from_definitions(
    definitions: Iterable[Tuple[str, str, Dict[str, Any]]],
    registry: Optional[SensorRegistry] = None,
) -> List[SensorPlugin]:
    """Instantiate plugins described by ``definitions``.

    Parameters
    ----------
    definitions:
        Iterable of ``(plugin_name, instance_name, config)`` tuples.
    registry:
        Optional :class:`SensorRegistry` to use.  When ``None`` a temporary
        registry that knows about entry points is used.
    """

    registry = registry or SensorRegistry()
    instances: List[SensorPlugin] = []
    for plugin_name, instance_name, config in definitions:
        try:
            plugin = registry.create(plugin_name, instance_name, config)
        except KeyError:
            # Allow fully qualified module paths as a fallback for ad-hoc sensors.
            plugin_cls = import_from_string(plugin_name)
            registry.register(plugin_cls)
            plugin = plugin_cls(name=instance_name, config=config)
        instances.append(plugin)
    return instances


class DummyTemperatureSensor(SensorPlugin):
    """Simple example sensor returning a fixed temperature value."""

    plugin_name = "dummy.temperature"

    def read(self) -> Any:
        baseline = float(self.config.get("baseline", 21.0))
        return baseline


def list_sensor_plugins(registry: Optional[SensorRegistry] = None) -> List[str]:
    """Convenience wrapper returning available sensor plugin identifiers."""

    registry = registry or SensorRegistry()
    return registry.available()


def list_sensor_plugin_metadata(registry: Optional[SensorRegistry] = None) -> List[Dict[str, Any]]:
    """Return metadata for every available sensor plugin."""

    registry = registry or SensorRegistry()
    return registry.describe_all()


class ActuatorRegistry:
    """Simple registry for actuator plugins."""

    def __init__(self) -> None:
        self._plugins: Dict[str, Type[ActuatorPlugin]] = {}

    def register(self, plugin: Type[ActuatorPlugin]) -> None:
        name = getattr(plugin, "plugin_name", None) or plugin.__name__
        if not name:
            raise ValueError("Actuator plugins must define plugin_name")
        self._plugins[name] = plugin

    def get(self, name: str) -> Type[ActuatorPlugin]:
        if name not in self._plugins:
            raise KeyError(f"Unknown actuator plugin: {name}")
        return self._plugins[name]

    def available(self) -> List[str]:
        return sorted(self._plugins)

    def create(self, plugin_name: str, name: str, config: Optional[Dict[str, Any]] = None) -> ActuatorPlugin:
        plugin_cls = self.get(plugin_name)
        return plugin_cls(name=name, config=config)


__all__ = [
    "ActuatorPlugin",
    "ActuatorRegistry",
    "DummyTemperatureSensor",
    "SensorPlugin",
    "SensorReading",
    "SensorRegistry",
    "import_from_string",
    "list_sensor_plugin_metadata",
    "list_sensor_plugins",
    "load_plugins_from_definitions",
]

