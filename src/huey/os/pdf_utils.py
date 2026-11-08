"""Compatibility shim exposing legacy huey.pdf_utils via huey.os.pdf_utils."""

from huey import pdf_utils as _implementation

__all__ = list(
    getattr(
        _implementation,
        "__all__",
        (name for name in vars(_implementation) if not name.startswith("_")),
    )
)
globals().update({name: getattr(_implementation, name) for name in __all__})
