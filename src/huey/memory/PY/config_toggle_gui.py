# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Config Toggle Gui module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.12.2025
# ==================================================
"""Simple GUI for toggling common configuration options."""

from __future__ import annotations

import os
from pathlib import Path

try:  # pragma: no cover - optional dependency
    import tkinter as tk
    from tkinter import messagebox
except Exception:  # pragma: no cover - can't import GUI libs
    tk = None
    messagebox = None

from huey.gui.tk import apply_root_chrome, primary_button_kwargs, tk_palette

from .config_manager import ConfigManager

DEFAULT_CONFIG = "config/pygpt_net/config.json"

_PALETTE = tk_palette()
DARK_BG = _PALETTE["background"]
PANEL_BG = _PALETTE["panel"]
PANEL_ALT_BG = _PALETTE["panel_alt"]
LIGHT_FG = _PALETTE["text"]
MUTED_FG = _PALETTE["muted_text"]
BORDER = _PALETTE["border"]

TOGGLE_FIELDS = {
    "access.voice_control": "Voice Control",
    "access.audio.event.speech": "Speech Synthesis",
    "access.microphone.notify": "Microphone Notify",
    "access.audio.notify.execute": "Audio Execute",
    "access.audio.use_cache": "Use Audio Cache",
}


def update_toggle_settings(config_path: str | Path, settings: dict[str, bool]) -> None:
    """Update boolean settings in ``config_path``."""
    manager = ConfigManager(str(config_path))
    manager.update_settings(settings)


def run_config_toggle_gui(config_path: str | Path = DEFAULT_CONFIG) -> None:
    """Display a window with checkboxes for common toggles."""
    if tk is None:
        raise RuntimeError("tkinter is not available")

    manager = ConfigManager(str(config_path))

    root = tk.Tk()
    apply_root_chrome(
        root,
        title="HueyOS Runtime Toggles",
        minsize=(420, 360),
        screen_mode=os.environ.get("SCREEN_MODE", "1080p"),
    )

    shell = tk.Frame(root, bg=DARK_BG)
    shell.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    header = tk.Frame(
        shell,
        bg=PANEL_BG,
        highlightbackground=BORDER,
        highlightcolor=BORDER,
        highlightthickness=1,
        bd=0,
    )
    header.pack(fill=tk.X, pady=(0, 10))
    tk.Label(
        header,
        text="HueyOS Runtime Toggles",
        bg=PANEL_BG,
        fg=LIGHT_FG,
        font=("Segoe UI", 16, "bold"),
        anchor="w",
    ).pack(fill=tk.X, padx=18, pady=(16, 6))
    tk.Label(
        header,
        text=(
            "Adjust the most common runtime switches here, save them to the "
            "shared configuration file, and return to the control deck."
        ),
        bg=PANEL_BG,
        fg=MUTED_FG,
        justify=tk.LEFT,
        wraplength=360,
    ).pack(fill=tk.X, padx=18, pady=(0, 16))

    body = tk.Frame(
        shell,
        bg=PANEL_BG,
        highlightbackground=BORDER,
        highlightcolor=BORDER,
        highlightthickness=1,
        bd=0,
    )
    body.pack(fill=tk.BOTH, expand=True)

    vars: dict[str, tk.BooleanVar] = {}
    tk.Label(
        body,
        text="Available toggles",
        bg=PANEL_BG,
        fg=LIGHT_FG,
        font=("Segoe UI", 12, "bold"),
        anchor="w",
    ).pack(fill=tk.X, padx=18, pady=(16, 6))
    tk.Label(
        body,
        text=f"Config path: {config_path}",
        bg=PANEL_BG,
        fg=MUTED_FG,
        justify=tk.LEFT,
        wraplength=360,
    ).pack(fill=tk.X, padx=18, pady=(0, 10))
    for key, label in TOGGLE_FIELDS.items():
        var = tk.BooleanVar(value=bool(manager.get_setting(key, False)))
        chk = tk.Checkbutton(
            body,
            text=label,
            variable=var,
            bg=PANEL_ALT_BG,
            fg=LIGHT_FG,
            selectcolor=_PALETTE["accent"],
            activebackground=PANEL_ALT_BG,
            activeforeground=LIGHT_FG,
            anchor="w",
            justify=tk.LEFT,
            padx=12,
            pady=8,
            highlightbackground=BORDER,
            highlightcolor=BORDER,
            highlightthickness=1,
        )
        chk.pack(fill=tk.X, padx=18, pady=(0, 8))
        vars[key] = var

    status_var = tk.StringVar(value="Ready")
    tk.Label(body, textvariable=status_var, bg=PANEL_BG, fg=MUTED_FG).pack(
        anchor="w", padx=18, pady=(4, 10)
    )

    def on_save() -> None:
        data = {k: v.get() for k, v in vars.items()}
        update_toggle_settings(config_path, data)
        status_var.set("Saved")
        if messagebox is not None:
            messagebox.showinfo("Config", "Settings saved.")
        root.destroy()

    button_row = tk.Frame(body, bg=PANEL_BG)
    button_row.pack(fill=tk.X, padx=18, pady=(0, 18))

    tk.Button(
        button_row,
        text="Save",
        command=on_save,
        **primary_button_kwargs(),
    ).pack(side=tk.LEFT)

    tk.Button(
        button_row,
        text="Cancel",
        command=root.destroy,
        **primary_button_kwargs(),
    ).pack(side=tk.LEFT, padx=(8, 0))

    root.mainloop()


__all__ = ["run_config_toggle_gui", "update_toggle_settings"]
