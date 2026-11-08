"""Compatibility module exposing :mod:`huey.pygpt_custom_cli` under :mod:`hueyos`."""

from importlib import import_module as _import_module

_implementation = _import_module("huey.pygpt_custom_cli")
__all__ = list(
    getattr(
        _implementation,
        "__all__",
        (name for name in vars(_implementation) if not name.startswith("_")),
    )
)
globals().update({name: getattr(_implementation, name) for name in __all__})
