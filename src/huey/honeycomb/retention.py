"""Compatibility shim forwarding to :mod:`hueyos.honeycomb.retention`."""

from hueyos.honeycomb.retention import RetentionPolicy, parse_duration

__all__ = ["RetentionPolicy", "parse_duration"]
