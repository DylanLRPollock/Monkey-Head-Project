# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Simple Chat Gui module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.12.2025
# ==================================================
"""Minimal Tkinter chat demonstration."""

from __future__ import annotations

import os

try:  # pragma: no cover - optional dependency
    import tkinter as tk
    from tkinter import scrolledtext
except Exception:  # pragma: no cover - can't import GUI libs
    tk = None
    scrolledtext = None

from .gui_scaling import apply_scaling
from .license_gui import ACCENT_PURPLE, DARK_BG, LIGHT_FG


def get_answer(question: str) -> str:
    """Return a canned response to ``question``."""
    q = question.lower().strip()
    if "capital of france" in q:
        return "The capital of France is Paris."
    if "2+2" in q or "two plus two" in q:
        return "2 + 2 equals 4."
    return "Sorry, I do not know the answer."


def run_simple_chat() -> None:
    """Launch a simple chat GUI using Tkinter."""
    if tk is None or scrolledtext is None:
        raise RuntimeError("tkinter is not available")

    root = tk.Tk()
    apply_scaling(root, os.environ.get("SCREEN_MODE", "1080p"))
    root.configure(bg=DARK_BG)
    root.title("Simple Chat Demo")

    entry = tk.Entry(root, width=60, bg=DARK_BG, fg=LIGHT_FG, insertbackground=LIGHT_FG)
    entry.pack(padx=10, pady=5)

    chat_box = scrolledtext.ScrolledText(
        root, width=70, height=15, bg=DARK_BG, fg=LIGHT_FG, state=tk.DISABLED
    )
    chat_box.pack(padx=10, pady=5)

    def on_ask() -> None:
        question = entry.get()
        if not question:
            return
        answer = get_answer(question)
        chat_box.config(state=tk.NORMAL)
        chat_box.insert(tk.END, f"Q: {question}\n")
        chat_box.insert(tk.END, f"A: {answer}\n\n")
        chat_box.config(state=tk.DISABLED)
        entry.delete(0, tk.END)

    button = tk.Button(root, text="Ask", command=on_ask, bg=ACCENT_PURPLE, fg=LIGHT_FG)
    button.pack(pady=5)

    root.mainloop()


__all__ = ["get_answer", "run_simple_chat"]
