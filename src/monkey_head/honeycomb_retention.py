"""Compatibility shim forwarding to :mod:`monkey_head.honeycomb.retention`."""

from __future__ import annotations

from monkey_head.honeycomb.retention import RetentionPolicy, parse_duration

__all__ = ["RetentionPolicy", "parse_duration"]
