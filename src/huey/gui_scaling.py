"""Apply scaling settings to a Tkinter root window."""

from __future__ import annotations

import os

try:  # pragma: no cover - optional in headless environments
    import tkinter.font as tkfont
except Exception:  # pragma: no cover
    tkfont = None  # type: ignore[assignment]


def _scale_for_mode(mode: str) -> tuple[float, int]:
    if mode == "4k":
        return 2.0, 14
    if mode == "custom":
        try:
            factor = float(os.environ.get("SCREEN_FACTOR", "1.0"))
        except ValueError:
            factor = 1.0
        try:
            size = int(float(os.environ.get("SCREEN_FONT_SIZE", "10")))
        except ValueError:
            size = 10
        return factor, size
    return 1.0, 10


def apply_scaling(root, mode: str = "1080p") -> None:
    factor, font_size = _scale_for_mode(mode)
    font_family = os.environ.get("SCREEN_FONT_FAMILY") if mode == "custom" else None

    try:
        root.tk.call("tk", "scaling", factor)
    except Exception:
        return
    if tkfont is None:
        return
    for name in ("TkDefaultFont", "TkTextFont", "TkFixedFont"):
        try:
            font = tkfont.nametofont(name)
            family = font_family
            if family is None and hasattr(font, "cget"):
                family = font.cget("family")
            kwargs = {"size": font_size}
            if family:
                kwargs["family"] = family
            font.configure(**kwargs)
        except Exception:
            continue


__all__ = ["apply_scaling"]
