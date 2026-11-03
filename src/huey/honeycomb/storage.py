"""Compatibility shim forwarding to :mod:`huey.os.honeycomb.storage`."""

from huey.os.honeycomb.storage import SCHEMA_VERSION, HoneycombRecord, HoneycombStorage

__all__ = ["SCHEMA_VERSION", "HoneycombRecord", "HoneycombStorage"]
