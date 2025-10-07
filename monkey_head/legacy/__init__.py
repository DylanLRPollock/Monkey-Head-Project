"""Legacy hardware integration helpers for HueyOS."""

from .connectors import (
    EmulatedLegacyConnector,
    LegacyConnector,
    LegacyConnectorFactory,
    SerialLegacyConnector,
)

__all__ = [
    "EmulatedLegacyConnector",
    "LegacyConnector",
    "LegacyConnectorFactory",
    "SerialLegacyConnector",
]
