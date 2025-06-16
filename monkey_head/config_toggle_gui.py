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

from .config_manager import ConfigManager
from .gui_scaling import apply_scaling
from .license_gui import DARK_BG, LIGHT_FG, ACCENT_PURPLE

DEFAULT_CONFIG = "config/pygpt_net/config.json"

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
    apply_scaling(root, os.environ.get("SCREEN_MODE", "1080p"))
    root.title("Config Toggles")
    root.configure(bg=DARK_BG)

    vars: dict[str, tk.BooleanVar] = {}
    for key, label in TOGGLE_FIELDS.items():
        var = tk.BooleanVar(value=bool(manager.get_setting(key, False)))
        chk = tk.Checkbutton(
            root,
            text=label,
            variable=var,
            bg=DARK_BG,
            fg=LIGHT_FG,
            selectcolor=ACCENT_PURPLE,
            activebackground=DARK_BG,
            activeforeground=LIGHT_FG,
        )
        chk.pack(anchor="w", padx=10, pady=5)
        vars[key] = var

    def on_save() -> None:
        data = {k: v.get() for k, v in vars.items()}
        update_toggle_settings(config_path, data)
        if messagebox is not None:
            messagebox.showinfo("Config", "Settings saved.")
        root.destroy()

    tk.Button(
        root,
        text="Save",
        command=on_save,
        bg=ACCENT_PURPLE,
        fg=LIGHT_FG,
        activebackground=ACCENT_PURPLE,
        activeforeground=LIGHT_FG,
    ).pack(pady=10)

    root.mainloop()


__all__ = ["run_config_toggle_gui", "update_toggle_settings"]
