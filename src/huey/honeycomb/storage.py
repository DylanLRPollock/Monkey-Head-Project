"""Compatibility shim forwarding to :mod:`hueyos.honeycomb.storage`."""

from hueyos.honeycomb.storage import SCHEMA_VERSION, HoneycombRecord, HoneycombStorage

__all__ = ["HoneycombStorage", "HoneycombRecord", "SCHEMA_VERSION"]
