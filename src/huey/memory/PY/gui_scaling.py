# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Gui Scaling module (huey/memory/PY)

"""Utilities for scaling Tkinter GUIs on high-DPI displays."""

import logging
import os

try:
    import tkinter as tk  # pragma: no cover - optional dependency
    from tkinter import font as tkfont
except ImportError:  # pragma: no cover - can't import GUI libs
    tk = None
    tkfont = None

logger = logging.getLogger(__name__)


def apply_scaling(root: "tk.Tk", mode: str = "4k") -> None:
    """Apply global scaling based on the selected display mode.

    Parameters
    ----------
    root: tk.Tk
        The root window instance.
    mode: str, optional
        ``"1080p"``, ``"4k"`` or ``"custom"`` to adjust scaling
        appropriately. ``"custom"`` reads ``SCREEN_FACTOR``,
        ``SCREEN_FONT_SIZE`` and ``SCREEN_FONT_FAMILY`` from the
        environment. Defaults to ``"4k"``.
    """
    if tk is None or tkfont is None:
        return

    mode = (mode or "4k").lower()
    font_family = os.environ.get("SCREEN_FONT_FAMILY", "Lato")

    if mode == "1080p":
        factor = 1.0
        font_size = 10
    elif mode == "custom":
        try:
            factor = float(os.environ.get("SCREEN_FACTOR", 1.5))
        except (ValueError, TypeError):
            factor = 1.5
        try:
            font_size = int(float(os.environ.get("SCREEN_FONT_SIZE", 12)))
        except (ValueError, TypeError):
            font_size = 12
        font_family = os.environ.get("SCREEN_FONT_FAMILY", font_family)
    else:
        factor = 2.0
        font_size = 14

    try:
        root.tk.call("tk", "scaling", factor)
    except (RuntimeError, AttributeError, TypeError) as e:
        logger.debug(f"Failed to apply scaling: {e}")

    for name in ("TkDefaultFont", "TkTextFont", "TkFixedFont", "TkMenuFont"):
        try:
            f = tkfont.nametofont(name)
            f.configure(size=font_size, family=font_family)
        except (RuntimeError, ValueError, AttributeError, TypeError) as e:
            logger.debug(f"Failed to configure font {name}: {e}")
            continue


__all__ = ["apply_scaling"]
