"""Compatibility shim forwarding to :mod:`hueyos.honeycomb.storage`."""

from hueyos.honeycomb.storage import HoneycombRecord, HoneycombStorage, SCHEMA_VERSION

__all__ = ["HoneycombStorage", "HoneycombRecord", "SCHEMA_VERSION"]
