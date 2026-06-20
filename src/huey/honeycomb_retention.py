"""Compatibility shim forwarding to :mod:`huey.os.honeycomb.retention`."""

from __future__ import annotations

from huey.os.honeycomb.retention import RetentionPolicy, parse_duration

__all__ = ["RetentionPolicy", "parse_duration"]
