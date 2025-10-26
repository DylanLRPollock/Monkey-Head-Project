# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Package initializer for huey/network

"""Network management utilities with wired-first preference."""

from .manager import NetworkManager, NetworkStatus

__all__ = ["NetworkManager", "NetworkStatus"]
