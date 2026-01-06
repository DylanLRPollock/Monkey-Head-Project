"""Legacy import path forwarding to :mod:`huey.honeycomb.storage`."""

from __future__ import annotations

from huey.honeycomb.storage import HoneycombRecord, HoneycombStorage

__all__ = ["HoneycombRecord", "HoneycombStorage"]
