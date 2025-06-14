# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.12.2025
# ==================================================
"""Simple Tkinter interface for :class:`AIProcessor`."""

from __future__ import annotations

import os

try:  # pragma: no cover - optional dependency
    import tkinter as tk
    from tkinter import messagebox
except Exception:  # pragma: no cover - can't import GUI libs
    tk = None
    messagebox = None

from .ai_processor import AIProcessor
from .gui_scaling import apply_scaling
from .license_gui import DARK_BG, LIGHT_FG, ACCENT_PURPLE


def run_ai_tools() -> None:
    """Launch a basic GUI exposing :class:`AIProcessor` methods."""
    if tk is None or messagebox is None:
        raise RuntimeError("tkinter is not available")

    proc = AIProcessor()

    root = tk.Tk()
    apply_scaling(root, os.environ.get("SCREEN_MODE", "1080p"))
    root.title("AI Tools")
    root.configure(bg=DARK_BG)

    tk.Label(root, text="Input Text", bg=DARK_BG, fg=LIGHT_FG).pack(padx=5, pady=5)
    text_entry = tk.Entry(
        root, width=50, bg=DARK_BG, fg=LIGHT_FG, insertbackground=LIGHT_FG
    )
    text_entry.pack(padx=5, pady=5)

    def on_process() -> None:
        text = text_entry.get()
        result = proc.process_data(text)
        messagebox.showinfo("Processed", result)

    tk.Button(
        root, text="Process", command=on_process, bg=ACCENT_PURPLE, fg=LIGHT_FG
    ).pack(pady=5)

    tk.Label(root, text="Numbers (comma separated)", bg=DARK_BG, fg=LIGHT_FG).pack(
        padx=5, pady=5
    )
    num_entry = tk.Entry(
        root, width=50, bg=DARK_BG, fg=LIGHT_FG, insertbackground=LIGHT_FG
    )
    num_entry.pack(padx=5, pady=5)

    def on_mean() -> None:
        raw = num_entry.get()
        try:
            nums = [float(x.strip()) for x in raw.split(",") if x.strip()]
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers")
            return
        result = proc.compute_mean(nums) if nums else 0.0
        messagebox.showinfo("Mean", str(result))

    tk.Button(
        root, text="Compute Mean", command=on_mean, bg=ACCENT_PURPLE, fg=LIGHT_FG
    ).pack(pady=5)

    root.mainloop()


__all__ = ["run_ai_tools"]
