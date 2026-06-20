# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Power module (src/huey/os)

"""Power management helpers bridging to :mod:`huey.power.management`."""

from __future__ import annotations

import sys
from importlib import import_module
from types import ModuleType
from typing import Any

_impl = import_module("huey.power.management")

__all__ = list(getattr(_impl, "__all__", ("BatteryMonitor", "PowerEvent")))

for name in __all__:
    globals()[name] = getattr(_impl, name)


def __getattr__(name: str) -> Any:
    return getattr(_impl, name)


_management_module = ModuleType(f"{__name__}.management")
for exported in __all__:
    setattr(_management_module, exported, globals()[exported])
_management_module.__all__ = list(__all__)
_management_module.__doc__ = _impl.__doc__
sys.modules[f"{__name__}.management"] = _management_module
