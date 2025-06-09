# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
from pathlib import Path

try:  # pragma: no cover - optional dependency
    import tkinter as tk
    from tkinter import messagebox, scrolledtext
except Exception:  # pragma: no cover - can't import GUI libs
    tk = None
    messagebox = None
    scrolledtext = None

from .config_manager import ConfigManager


def accept_license(config_path: str | Path) -> None:
    """Set the ``license.accepted`` flag in the given config file."""
    manager = ConfigManager(str(config_path))
    manager.set_setting("license.accepted", True)


def show_license_gui(config_path: str | Path = "config/pygpt_net/config.json") -> None:
    """Display a simple license agreement dialog."""
    if tk is None:
        raise RuntimeError("tkinter is not available")

    manager = ConfigManager(str(config_path))
    if manager.get_setting("license.accepted"):
        return

    root = tk.Tk()
    root.title("License Agreement")

    text = scrolledtext.ScrolledText(root, width=80, height=20, wrap=tk.WORD)
    try:
        license_text = Path("docs/LICENSE").read_text(encoding="utf-8")
    except Exception:
        license_text = "License file not found."
    text.insert(tk.END, license_text)
    text.config(state=tk.DISABLED)
    text.pack(padx=10, pady=10)

    def on_accept() -> None:
        accept_license(config_path)
        messagebox.showinfo("License", "License accepted")
        root.destroy()

    def on_decline() -> None:
        messagebox.showwarning("License", "You must accept the license to proceed")
        root.destroy()

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="Accept", command=on_accept).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Decline", command=on_decline).pack(side=tk.LEFT, padx=5)

    root.mainloop()


if __name__ == "__main__":
    show_license_gui()
