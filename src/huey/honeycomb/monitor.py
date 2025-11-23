"""Compatibility shim forwarding to :mod:`hueyos.honeycomb.monitor`."""

from hueyos.honeycomb.monitor import HoneycombMonitor, HoneycombUsageTotals

__all__ = ["HoneycombMonitor", "HoneycombUsageTotals"]
