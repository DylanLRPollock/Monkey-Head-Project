"""Utilities for scaling Tkinter GUIs on high-DPI displays."""

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
        ``"1080p"`` or ``"4k"`` to adjust scaling appropriately. Defaults to
        ``"4k"``.
    """
    if tk is None or tkfont is None:
        return

    mode = (mode or "4k").lower()
    if mode == "1080p":
        factor = 1.0
        font_size = 10
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
