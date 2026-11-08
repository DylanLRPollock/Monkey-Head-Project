"""Compatibility shim exposing legacy huey.core.task_scheduler
via huey.os.core.task_scheduler."""

from huey.core import task_scheduler as _implementation

__all__ = list(
    getattr(
        _implementation,
        "__all__",
        (name for name in vars(_implementation) if not name.startswith("_")),
    )
)
globals().update({name: getattr(_implementation, name) for name in __all__})
