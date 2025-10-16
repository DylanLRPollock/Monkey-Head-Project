# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Manager module (huey/hardware)

"""Sensor manager coordinating plugin lifecycle and telemetry logging."""

from __future__ import annotations

import asyncio
import logging
import threading
import uuid
from collections.abc import AsyncIterator
from contextlib import suppress
from typing import Any, Dict, Iterable, List, Optional, Tuple

from monkey_head.honeycomb_storage import HoneycombStorage
from monkey_head.utils.persistence import TelemetryStore

from .plugins import (
    ActuatorPlugin,
    ActuatorRegistry,
    SensorPlugin,
    SensorReading,
    SensorRegistry,
    load_plugins_from_definitions,
)

LOGGER = logging.getLogger(__name__)


class SensorManager:
    """Runtime container for configured sensor plugins."""

    def __init__(
        self,
        *,
        storage: Optional[HoneycombStorage] = None,
        registry: Optional[SensorRegistry] = None,
        telemetry_store: Optional[TelemetryStore] = None,
    ) -> None:
        self.storage = storage or HoneycombStorage()
        self.registry = registry or SensorRegistry()
        self.telemetry_store = telemetry_store
        self._sensors: Dict[str, SensorPlugin] = {}
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._subscribers: List[Tuple[Optional[str], asyncio.Queue[SensorReading]]] = []

    # ------------------------------------------------------------------
    # Sensor lifecycle
    # ------------------------------------------------------------------
    def add_sensor(self, plugin_name: str, name: str, config: Optional[Dict[str, Any]] = None) -> SensorPlugin:
        """Instantiate and register a sensor using ``plugin_name``."""

        with self._lock:
            plugin = self.registry.create(plugin_name, name, config)
            plugin.setup()
            self._sensors[name] = plugin
            self._configs[name] = plugin.config.copy()
        LOGGER.info("Registered sensor %s using plugin %s", name, plugin_name)
        return plugin

    def add_plugins(self, definitions: Iterable[Tuple[str, str, Dict[str, Any]]]) -> List[SensorPlugin]:
        """Bulk register sensors from configuration definitions."""

        sensors = load_plugins_from_definitions(definitions, registry=self.registry)
        for sensor in sensors:
            self.register_instance(sensor)
        return sensors

    def register_instance(self, sensor: SensorPlugin) -> None:
        """Register an already instantiated ``sensor``."""

        with self._lock:
            sensor.setup()
            self._sensors[sensor.name] = sensor
            self._configs[sensor.name] = sensor.config.copy()
        LOGGER.info("Registered sensor %s using pre-instantiated plugin", sensor.name)

    def remove_sensor(self, name: str) -> None:
        """Remove a sensor from the manager."""

        with self._lock:
            sensor = self._sensors.pop(name, None)
            self._configs.pop(name, None)
        if sensor:
            with suppress(Exception):
                sensor.shutdown()
            LOGGER.info("Removed sensor %s", name)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------
    def list_sensors(self) -> List[Dict[str, Any]]:
        """Return metadata about configured sensors."""

        metadata: List[Dict[str, Any]] = []
        with self._lock:
            for sensor in self._sensors.values():
                config_copy = sensor.config.copy()
                self._configs[sensor.name] = config_copy
                metadata.append(
                    sensor.provenance | {"name": sensor.name, "config": config_copy}
                )
        return metadata

    def get_sensor(self, name: str) -> Optional[SensorPlugin]:
        with self._lock:
            return self._sensors.get(name)

    # ------------------------------------------------------------------
    # Data acquisition
    # ------------------------------------------------------------------
    def poll_sensor(self, name: str) -> SensorReading:
        sensor = self.get_sensor(name)
        if not sensor:
            raise KeyError(f"Unknown sensor {name}")
        reading = sensor.capture()
        self._record_reading(reading)
        return reading

    def poll_all(self) -> List[SensorReading]:
        readings: List[SensorReading] = []
        with self._lock:
            sensors = list(self._sensors.values())
        for sensor in sensors:
            try:
                reading = sensor.capture()
            except Exception:
                LOGGER.exception("Sensor %s failed to capture reading", sensor.name)
                continue
            self._record_reading(reading)
            readings.append(reading)
        return readings

    def _record_reading(self, reading: SensorReading) -> None:
        payload = {
            "name": reading.name,
            "value": reading.value,
            "timestamp": reading.timestamp,
            "provenance": reading.provenance,
        }
        key = f"telemetry/sensor/{reading.name}/{uuid.uuid4().hex}"
        self.storage.store(key, payload)
        if self.telemetry_store is not None:
            try:
                self.telemetry_store.log_sensor_reading(reading)
            except Exception:  # pragma: no cover - logging only
                LOGGER.exception("Failed to persist sensor reading to telemetry store")
        self._broadcast(reading)

    # ------------------------------------------------------------------
    # Streaming helpers
    # ------------------------------------------------------------------
    def subscribe(self, sensor_name: Optional[str] = None) -> asyncio.Queue[SensorReading]:
        queue: asyncio.Queue[SensorReading] = asyncio.Queue()
        self._subscribers.append((sensor_name, queue))
        return queue

    def unsubscribe(self, queue: asyncio.Queue[SensorReading]) -> None:
        self._subscribers = [item for item in self._subscribers if item[1] is not queue]

    def _broadcast(self, reading: SensorReading) -> None:
        for sensor_name, queue in list(self._subscribers):
            if sensor_name and sensor_name != reading.name:
                continue
            try:
                queue.put_nowait(reading)
            except asyncio.QueueFull:  # pragma: no cover - best effort delivery
                LOGGER.debug("Dropping sensor reading for %s due to full queue", reading.name)

    async def stream(self, sensor_name: Optional[str] = None) -> AsyncIterator[SensorReading]:
        """Yield readings in real-time for ``sensor_name`` or all sensors.

        This helper wraps :meth:`subscribe` to provide an asynchronous iterator
        that automatically unsubscribes when the consumer stops iterating.
        """

        queue = self.subscribe(sensor_name)
        try:
            while True:
                reading = await queue.get()
                yield reading
        finally:
            self.unsubscribe(queue)

    # ------------------------------------------------------------------
    # Historical queries
    # ------------------------------------------------------------------
    def load_history(self, sensor_name: str, *, limit: int = 50) -> List[Dict[str, Any]]:
        prefix = f"telemetry/sensor/{sensor_name}/"
        keys = self.storage.list_keys(prefix=prefix)
        if limit:
            keys = keys[-limit:]
        history: List[Dict[str, Any]] = []
        for key in keys:
            record = self.storage.get_record(key)
            if not record:
                continue
            payload = record.data
            payload.setdefault("key", key)
            history.append(payload)
        history.sort(key=lambda item: item.get("timestamp", 0))
        return history


class ActuatorManager:
    """Lightweight manager for actuator plugins."""

    def __init__(self, *, registry: Optional[ActuatorRegistry] = None) -> None:
        self.registry = registry or ActuatorRegistry()
        self._actuators: Dict[str, ActuatorPlugin] = {}
        self._lock = threading.RLock()

    def add_actuator(self, plugin_name: str, name: str, config: Optional[Dict[str, Any]] = None) -> ActuatorPlugin:
        with self._lock:
            plugin = self.registry.create(plugin_name, name, config)
            plugin.setup()
            self._actuators[name] = plugin
        LOGGER.info("Registered actuator %s using plugin %s", name, plugin_name)
        return plugin

    def register_instance(self, actuator: ActuatorPlugin) -> None:
        with self._lock:
            actuator.setup()
            self._actuators[actuator.name] = actuator
        LOGGER.info("Registered actuator %s using pre-instantiated plugin", actuator.name)

    def remove_actuator(self, name: str) -> None:
        with self._lock:
            actuator = self._actuators.pop(name, None)
        if actuator:
            with suppress(Exception):
                actuator.shutdown()
            LOGGER.info("Removed actuator %s", name)

    def list_actuators(self) -> List[Dict[str, Any]]:
        with self._lock:
            actuators = list(self._actuators.values())
        return [actuator.provenance | {"name": actuator.name} for actuator in actuators]

    def perform(self, name: str, command: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        with self._lock:
            actuator = self._actuators.get(name)
        if actuator is None:
            raise KeyError(f"Unknown actuator {name}")
        with actuator._lock:  # type: ignore[attr-defined]
            return actuator.perform(command, payload)


def create_default_sensor_manager(*, telemetry_store: Optional[TelemetryStore] = None) -> SensorManager:
    """Create a :class:`SensorManager` with built-in plugins registered."""

    from . import drivers  # Local import to avoid circular dependency

    registry = SensorRegistry()
    drivers.register_builtin_sensors(registry)
    return SensorManager(
        storage=HoneycombStorage(),
        registry=registry,
        telemetry_store=telemetry_store,
    )


def create_default_actuator_manager() -> ActuatorManager:
    """Create an :class:`ActuatorManager` with built-in plugins registered."""

    from . import drivers  # Local import to avoid circular dependency

    registry = ActuatorRegistry()
    drivers.register_builtin_actuators(registry)
    return ActuatorManager(registry=registry)


__all__ = [
    "ActuatorManager",
    "SensorManager",
    "create_default_actuator_manager",
    "create_default_sensor_manager",
]

