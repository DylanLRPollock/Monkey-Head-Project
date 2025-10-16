# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Package initializer for huey/legacy

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
