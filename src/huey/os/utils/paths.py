"""Compatibility shim exposing legacy huey.utils.paths via huey.os.utils.paths."""

from huey.utils import paths as _implementation

__all__ = list(
    getattr(
        _implementation,
        "__all__",
        (name for name in vars(_implementation) if not name.startswith("_")),
    )
)
globals().update({name: getattr(_implementation, name) for name in __all__})
