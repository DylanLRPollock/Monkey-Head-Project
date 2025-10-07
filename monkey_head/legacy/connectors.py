"""Legacy system connector abstractions.

The HueyOS codex references Commodore and other retro systems that need to
interface with modern infrastructure. This module provides a thin layer
that can transparently operate in one of two modes:

* **Serial bridging** using USB/RS-232 interfaces for real hardware.
* **Emulation bridge** leveraging software emulators such as VICE.

The goal is to hide connection and transport details from higher level
callers while keeping the implementation fully testable in isolation.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Protocol

LOGGER = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    import serial  # type: ignore
except Exception:  # pragma: no cover - fallback when pyserial missing
    serial = None  # type: ignore[assignment]


class LegacyConnector(Protocol):
    """Abstract interface implemented by all legacy connectors."""

    async def connect(self) -> None:
        """Establish the connection to the legacy system."""

    async def send(self, payload: bytes) -> None:
        """Send raw bytes to the legacy system."""

    async def receive(self, size: int = 1024) -> bytes:
        """Receive bytes from the legacy system."""

    async def close(self) -> None:
        """Tear down the connection."""


@dataclass
class SerialLegacyConnector:
    """USB/serial bridge for physical VIC-20/C64/C128 hardware."""

    port: str
    baudrate: int = 9600
    timeout: float = 1.0
    _serial: Any = None

    async def connect(self) -> None:
        if serial is None:
            raise RuntimeError(
                "pyserial is required for SerialLegacyConnector but is not installed"
            )
        LOGGER.info("Opening serial connection to legacy system on %s", self.port)
        self._serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        await asyncio.sleep(0)

    async def send(self, payload: bytes) -> None:
        if self._serial is None:
            raise RuntimeError("Serial connection has not been initialised")
        LOGGER.debug("Writing %s bytes to legacy serial device", len(payload))
        self._serial.write(payload)
        await asyncio.sleep(0)

    async def receive(self, size: int = 1024) -> bytes:
        if self._serial is None:
            raise RuntimeError("Serial connection has not been initialised")
        data = self._serial.read(size)
        await asyncio.sleep(0)
        return data

    async def close(self) -> None:
        if self._serial is not None:
            LOGGER.info("Closing serial connection to %s", self.port)
            self._serial.close()
            self._serial = None
        await asyncio.sleep(0)


@dataclass
class EmulatedLegacyConnector:
    """Connector that proxies requests to a software emulator."""

    command_channel: asyncio.Queue[bytes] = field(init=False)
    response_channel: asyncio.Queue[bytes] = field(init=False)

    def __post_init__(self) -> None:
        self.command_channel = asyncio.Queue()
        self.response_channel = asyncio.Queue()

    async def connect(self) -> None:
        LOGGER.info("Initialising emulated legacy connector")
        await asyncio.sleep(0)

    async def send(self, payload: bytes) -> None:
        LOGGER.debug("Queueing %s bytes for emulator", len(payload))
        await self.command_channel.put(payload)

    async def receive(self, size: int = 1024) -> bytes:
        LOGGER.debug("Awaiting emulator response (max %s bytes)", size)
        data = await self.response_channel.get()
        return data[:size]

    async def close(self) -> None:
        LOGGER.info("Shutting down emulator connector queues")
        await asyncio.sleep(0)

    async def inject_emulator_response(self, payload: bytes) -> None:
        """Utility helper used by tests to simulate emulator output."""

        await self.response_channel.put(payload)


class LegacyConnectorFactory:
    """Factory for instantiating connectors based on configuration."""

    @staticmethod
    def create(config: Dict[str, Any]) -> LegacyConnector:
        mode = config.get("mode", "emulated").lower()
        if mode == "serial":
            return SerialLegacyConnector(
                port=config["port"],
                baudrate=int(config.get("baudrate", 9600)),
                timeout=float(config.get("timeout", 1.0)),
            )
        if mode == "emulated":
            return EmulatedLegacyConnector()
        raise ValueError(f"Unsupported legacy connector mode: {mode}")
