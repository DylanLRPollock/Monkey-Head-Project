# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Network module (src/huey/os)

"""Network management helpers bridging to :mod:`huey.network.manager`."""

from __future__ import annotations

import sys
from importlib import import_module
from types import ModuleType
from typing import Any

_impl = import_module("huey.network.manager")

__all__ = list(getattr(_impl, "__all__", ("NetworkManager", "NetworkStatus")))

for name in __all__:
    globals()[name] = getattr(_impl, name)


def __getattr__(name: str) -> Any:
    return getattr(_impl, name)


_manager_module = ModuleType(f"{__name__}.manager")
for exported in __all__:
    setattr(_manager_module, exported, globals()[exported])
_manager_module.__all__ = list(__all__)
_manager_module.__doc__ = _impl.__doc__
sys.modules[f"{__name__}.manager"] = _manager_module
