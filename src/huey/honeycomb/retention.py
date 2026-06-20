"""Compatibility shim forwarding to :mod:`huey.os.honeycomb.retention`."""

from huey.os.honeycomb.retention import RetentionPolicy, parse_duration

__all__ = ["RetentionPolicy", "parse_duration"]
