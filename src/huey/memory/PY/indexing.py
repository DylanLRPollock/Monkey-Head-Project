"""Legacy alias for canonical huey.memory.indexing."""
from __future__ import annotations
import sys
from importlib import import_module

_impl = import_module("huey.memory.indexing")
if __name__ == "__main__":
    raise SystemExit("This module has no CLI; use scripts/memory_index.py")
else:
    sys.modules[__name__] = _impl
