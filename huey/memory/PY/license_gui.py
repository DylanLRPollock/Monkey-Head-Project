# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from pathlib import Path

try:  # pragma: no cover - optional dependency
    import tkinter as tk
    from tkinter import messagebox, scrolledtext
except Exception:  # pragma: no cover - can't import GUI libs
    tk = None
    messagebox = None
    scrolledtext = None

from .config_manager import ConfigManager
from .gui_scaling import apply_scaling

# Shared theme colors
DARK_BG = "#000000"  # black background
LIGHT_FG = "#00ff00"  # green text
ACCENT_PURPLE = "#2d2b57"  # dark purple accent


def accept_license(config_path: str | Path, license_hash: str | None = None) -> None:
    """Persist the acceptance state and timestamp for the license dialog."""

    manager = ConfigManager(str(config_path))
    payload = {
        "license.accepted": True,
        "license.accepted_at": datetime.utcnow().isoformat(timespec="seconds"),
    }
    if license_hash is not None:
        payload["license.hash"] = license_hash
    manager.update_settings(payload)


def show_license_gui(config_path: str | Path = "config/pygpt_net/config.json") -> None:
    """Display a simple license agreement dialog."""

    if tk is None or scrolledtext is None:
        raise RuntimeError("tkinter is not available")

    manager = ConfigManager(str(config_path))

    license_path = Path(__file__).resolve().parents[3] / "LICENSE"
    try:
        license_text = license_path.read_text(encoding="utf-8")
    except Exception:
        license_text = "License file not found."
    license_hash = sha256(license_text.encode("utf-8")).hexdigest()

    accepted = bool(manager.get_setting("license.accepted"))
    accepted_hash = manager.get_setting("license.hash")
    if accepted and accepted_hash == license_hash:
        return

    root = tk.Tk()
    apply_scaling(root)
    root.title("License Agreement")
    root.minsize(800, 600)
    root.configure(
        bg=DARK_BG,
        highlightbackground=ACCENT_PURPLE,
        highlightcolor=ACCENT_PURPLE,
        highlightthickness=2,
    )

    text = scrolledtext.ScrolledText(
        root,
        width=100,
        height=25,
        wrap=tk.WORD,
        bg=DARK_BG,
        fg=LIGHT_FG,
        insertbackground=LIGHT_FG,
        highlightbackground=ACCENT_PURPLE,
        highlightcolor=ACCENT_PURPLE,
        highlightthickness=2,
    )
    text.insert(tk.END, license_text)
    text.config(state=tk.DISABLED)
    text.pack(padx=10, pady=10)

    def on_accept() -> None:
        accept_license(config_path, license_hash)
        messagebox.showinfo("License", "License accepted")
        messagebox.showwarning(
            "Experimental",
            "This is experimental software. Proceed with caution.",
        )
        root.destroy()

    def on_decline() -> None:
        messagebox.showwarning("License", "You must accept the license to proceed")
        root.destroy()

    btn_frame = tk.Frame(
        root,
        bg=DARK_BG,
        highlightbackground=ACCENT_PURPLE,
        highlightcolor=ACCENT_PURPLE,
        highlightthickness=2,
    )
    btn_frame.pack(pady=10)
    tk.Button(
        btn_frame,
        text="Accept",
        command=on_accept,
        bg=ACCENT_PURPLE,
        fg=LIGHT_FG,
        activebackground=ACCENT_PURPLE,
        activeforeground=LIGHT_FG,
    ).pack(side=tk.LEFT, padx=5)
    tk.Button(
        btn_frame,
        text="Decline",
        command=on_decline,
        bg=ACCENT_PURPLE,
        fg=LIGHT_FG,
        activebackground=ACCENT_PURPLE,
        activeforeground=LIGHT_FG,
    ).pack(side=tk.LEFT, padx=5)

    root.mainloop()


if __name__ == "__main__":
    show_license_gui()
