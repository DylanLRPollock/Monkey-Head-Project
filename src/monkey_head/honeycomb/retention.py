"""Compatibility wrapper for :mod:`huey.honeycomb.retention`."""

from __future__ import annotations

from huey.honeycomb.retention import RetentionPolicy, parse_duration

__all__ = ["RetentionPolicy", "parse_duration"]
