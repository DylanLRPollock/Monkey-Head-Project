"""Legacy module alias for the canonical huey.memory.preload_data."""
from __future__ import annotations
import sys
from importlib import import_module
_impl = import_module("huey.memory.preload_data")
if __name__ == "__main__":
    _impl.main()
else:
    sys.modules[__name__] = _impl
