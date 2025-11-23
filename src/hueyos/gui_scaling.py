"""Apply scaling settings to a Tkinter root window."""

from __future__ import annotations

import os
import tkinter.font as tkfont


def _scale_for_mode(mode: str) -> tuple[float, int]:
    if mode == "4k":
        return 2.0, 14
    if mode == "custom":
        factor = float(os.environ.get("SCREEN_FACTOR", "1.0"))
        size = int(os.environ.get("SCREEN_FONT_SIZE", "10"))
        return factor, size
    return 1.0, 10


def apply_scaling(root, mode: str = "1080p") -> None:
    factor, font_size = _scale_for_mode(mode)
    font_family = os.environ.get("SCREEN_FONT_FAMILY") if mode == "custom" else None

    root.tk.call("tk", "scaling", factor)
    for name in ("TkDefaultFont", "TkTextFont", "TkFixedFont"):
        font = tkfont.nametofont(name)
        font.configure(size=font_size, family=font_family or font.cget("family"))


__all__ = ["apply_scaling"]
