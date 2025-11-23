"""Legacy connector bridges for HueyOS.

This package proxies calls into the legacy ``huey.legacy`` namespace while
keeping imports stable for callers that depend on the newer ``hueyos`` path.
"""
from __future__ import annotations

__all__ = ["connectors"]
