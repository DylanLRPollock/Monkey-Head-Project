"""Utilities for scaling Tkinter GUIs on high-DPI displays."""

try:
    import tkinter as tk  # pragma: no cover - optional dependency
    from tkinter import font as tkfont
except Exception:  # pragma: no cover - can't import GUI libs
    tk = None
    tkfont = None


def apply_scaling(root: "tk.Tk", factor: float = 2.0, font_size: int = 14) -> None:
    """Apply global scaling and increase default font sizes.

    Parameters
    ----------
    root: tk.Tk
        The root window instance.
    factor: float, optional
        Scaling factor for HiDPI displays. Default is ``2.0``.
    font_size: int, optional
        Base font size to apply. Default is ``14``.
    """
    if tk is None or tkfont is None:
        return

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
