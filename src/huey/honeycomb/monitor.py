"""Compatibility shim forwarding to :mod:`huey.os.honeycomb.monitor`."""

from huey.os.honeycomb.monitor import HoneycombMonitor, HoneycombUsageTotals

__all__ = ["HoneycombMonitor", "HoneycombUsageTotals"]
