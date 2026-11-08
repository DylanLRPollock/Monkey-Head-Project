"""Compatibility shim exposing legacy huey.hardware.plugins via huey.os.hardware.plugins."""

from huey.hardware import plugins as _implementation

__all__ = list(
    getattr(
        _implementation,
        "__all__",
        (name for name in vars(_implementation) if not name.startswith("_")),
    )
)
globals().update({name: getattr(_implementation, name) for name in __all__})
