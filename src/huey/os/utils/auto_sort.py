"""Compatibility shim exposing legacy huey.utils.auto_sort via huey.os.utils.auto_sort."""

from importlib import import_module as _import_module

_implementation = _import_module("huey.utils.auto_sort")
__all__ = list(
    getattr(
        _implementation,
        "__all__",
        (name for name in vars(_implementation) if not name.startswith("_")),
    )
)
globals().update({name: getattr(_implementation, name) for name in __all__})
