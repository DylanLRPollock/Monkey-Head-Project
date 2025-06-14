"""Utilities for scaling Tkinter GUIs on high-DPI displays."""

import os

try:
    import tkinter as tk  # pragma: no cover - optional dependency
    from tkinter import font as tkfont
except Exception:  # pragma: no cover - can't import GUI libs
    tk = None
    tkfont = None


def apply_scaling(root: "tk.Tk", mode: str = "4k") -> None:
    """Apply global scaling based on the selected display mode.

    Parameters
    ----------
    root: tk.Tk
        The root window instance.
    mode: str, optional
        ``"1080p"``, ``"4k"`` or ``"custom"`` to adjust scaling
        appropriately. ``"custom"`` reads ``SCREEN_FACTOR`` and
        ``SCREEN_FONT_SIZE`` from the environment. Defaults to ``"4k"``.
    """
    if tk is None or tkfont is None:
        return

    mode = (mode or "4k").lower()
    if mode == "1080p":
        factor = 1.0
        font_size = 10
    elif mode == "custom":
        try:
            factor = float(os.environ.get("SCREEN_FACTOR", 1.5))
        except Exception:
            factor = 1.5
        try:
            font_size = int(float(os.environ.get("SCREEN_FONT_SIZE", 12)))
        except Exception:
            font_size = 12
    else:
        factor = 2.0
        font_size = 14

    try:
        root.tk.call("tk", "scaling", factor)
    except Exception:
        pass

    for name in ("TkDefaultFont", "TkTextFont", "TkFixedFont", "TkMenuFont"):
        try:
            f = tkfont.nametofont(name)
            f.configure(size=font_size)
        except Exception:
            continue


__all__ = ["apply_scaling"]
