"""HueyOS API package.

Keep this package initializer lightweight so importing router modules such as
``hueyos.api.routers.system`` does not eagerly import the full legacy API app.
The concrete ASGI app remains available from ``hueyos.api.app``.
"""

from __future__ import annotations

__all__ = ["app", "main", "SCHEDULER"]


def __getattr__(name: str):
    if name in __all__:
        from . import app as _app_module

        value = getattr(_app_module, name)
        globals()[name] = value
        return value

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
