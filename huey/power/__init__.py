# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Package initializer for huey/power

"""Power management utilities for HueyOS."""

from .management import BatteryMonitor, PowerEvent

__all__ = ["BatteryMonitor", "PowerEvent"]
