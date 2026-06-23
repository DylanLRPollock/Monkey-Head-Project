"""Shared Tkinter chrome helpers for HueyOS GUI surfaces."""

from __future__ import annotations

import os
from typing import Any

from huey.gui.theme import as_tk_palette
from huey.gui_scaling import apply_scaling

_PALETTE = as_tk_palette()


def tk_palette() -> dict[str, str]:
    """Return a copy of the shared Tk palette."""

    return dict(_PALETTE)


def apply_root_chrome(
    root: Any,
    *,
    title: str,
    minsize: tuple[int, int] | None = None,
    screen_mode: str | None = None,
) -> None:
    """Apply shared HueyOS root-window styling."""

    mode = screen_mode or os.environ.get("SCREEN_MODE", "1080p")
    apply_scaling(root, mode)
    if hasattr(root, "title"):
        root.title(title)
    if minsize is not None and hasattr(root, "minsize"):
        root.minsize(*minsize)
    if hasattr(root, "configure"):
        root.configure(
            bg=_PALETTE["background"],
            highlightbackground=_PALETTE["border"],
            highlightcolor=_PALETTE["border"],
            highlightthickness=1,
        )


def apply_ttk_chrome(root: Any, ttk_module: Any) -> Any:
    """Apply shared ttk styling and return the created ``Style`` object."""

    style = ttk_module.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure(
        "TLabel",
        background=_PALETTE["background"],
        foreground=_PALETTE["text"],
    )
    style.configure(
        "TButton",
        background=_PALETTE["accent"],
        foreground=_PALETTE["text"],
        borderwidth=1,
    )
    style.map(
        "TButton",
        background=[
            ("active", _PALETTE["panel_alt"]),
            ("pressed", _PALETTE["success"]),
        ],
        foreground=[("active", _PALETTE["text"]), ("pressed", _PALETTE["text"])],
    )
    style.configure(
        "TNotebook",
        background=_PALETTE["background"],
        borderwidth=0,
    )
    style.configure(
        "TNotebook.Tab",
        background=_PALETTE["panel_alt"],
        foreground=_PALETTE["text"],
        padding=(12, 8),
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", _PALETTE["accent"])],
        foreground=[("selected", _PALETTE["text"])],
    )
    style.configure(
        "TProgressbar",
        troughcolor=_PALETTE["panel"],
        background=_PALETTE["success"],
        lightcolor=_PALETTE["success"],
        darkcolor=_PALETTE["success"],
        bordercolor=_PALETTE["border"],
    )
    style.configure(
        "TCombobox",
        fieldbackground=_PALETTE["panel_alt"],
        background=_PALETTE["panel_alt"],
        foreground=_PALETTE["text"],
    )
    return style


def primary_button_kwargs() -> dict[str, object]:
    """Return shared button styling kwargs."""

    return {
        "bg": _PALETTE["accent"],
        "fg": _PALETTE["text"],
        "activebackground": _PALETTE["panel_alt"],
        "activeforeground": _PALETTE["text"],
    }


def text_surface_kwargs(*, surface: str = "panel_alt") -> dict[str, object]:
    """Return shared text widget styling kwargs."""

    background = _PALETTE.get(surface, _PALETTE["panel_alt"])
    return {
        "bg": background,
        "fg": _PALETTE["text"],
        "insertbackground": _PALETTE["text"],
        "highlightbackground": _PALETTE["border"],
        "highlightcolor": _PALETTE["border"],
        "highlightthickness": 1,
    }


def listbox_kwargs(*, surface: str = "panel_alt") -> dict[str, object]:
    """Return shared listbox styling kwargs."""

    options = text_surface_kwargs(surface=surface)
    options["selectbackground"] = _PALETTE["accent"]
    options["selectforeground"] = _PALETTE["text"]
    return options


__all__ = [
    "apply_root_chrome",
    "apply_ttk_chrome",
    "listbox_kwargs",
    "primary_button_kwargs",
    "text_surface_kwargs",
    "tk_palette",
]
