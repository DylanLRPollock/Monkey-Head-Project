"""Legacy import alias for the canonical huey.v1.response_bridge module."""
from __future__ import annotations

import sys
from importlib import import_module

_impl = import_module("huey.v1.response_bridge")
if __name__ == "__main__":
    raise SystemExit(_impl.main())
else:
    sys.modules[__name__] = _impl
