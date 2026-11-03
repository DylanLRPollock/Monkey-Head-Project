"""Compatibility alias for huey.media.cli_audio_prepare."""
from __future__ import annotations
import sys
from importlib import import_module
_impl = import_module("huey.media.cli_audio_prepare")
if __name__ == "__main__":
    raise SystemExit(_impl.main())
else:
    sys.modules[__name__] = _impl
