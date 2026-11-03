"""Legacy module alias for :mod:`huey.memory.metadata`."""
from __future__ import annotations
import sys
from importlib import import_module

_impl = import_module("huey.memory.metadata")
if __name__ == "__main__":
    if hasattr(_impl, "main"):
        _impl.main()
    else:
        raise SystemExit("This module has no CLI; import it instead")
else:
    sys.modules[__name__] = _impl
