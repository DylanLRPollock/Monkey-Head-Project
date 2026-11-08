"""Compatibility shim exposing legacy huey.utils.auto_sort via huey.os.utils.auto_sort."""

from huey.utils import auto_sort as _implementation

__all__ = list(
    getattr(
        _implementation,
        "__all__",
        (name for name in vars(_implementation) if not name.startswith("_")),
    )
)
globals().update({name: getattr(_implementation, name) for name in __all__})
