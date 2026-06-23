# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: License Gui module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

try:  # pragma: no cover - optional dependency
    import tkinter as tk
    from tkinter import messagebox, scrolledtext
except Exception:  # pragma: no cover - can't import GUI libs
    tk = None
    messagebox = None
    scrolledtext = None

from huey.gui.tk import (
    apply_root_chrome,
    primary_button_kwargs,
    text_surface_kwargs,
    tk_palette,
)

from .config_manager import ConfigManager

_PALETTE = tk_palette()
DARK_BG = _PALETTE["background"]
PANEL_BG = _PALETTE["panel"]
PANEL_ALT_BG = _PALETTE["panel_alt"]
LIGHT_FG = _PALETTE["text"]
MUTED_FG = _PALETTE["muted_text"]
ACCENT_PURPLE = _PALETTE["accent"]
BORDER = _PALETTE["border"]


def accept_license(config_path: str | Path, license_hash: str | None = None) -> None:
    """Persist the acceptance state and timestamp for the license dialog."""

    manager = ConfigManager(str(config_path))
    payload = {
        "license.accepted": True,
        "license.accepted_at": datetime.now(tz=UTC).isoformat(timespec="seconds"),
    }
    if license_hash is not None:
        payload["license.hash"] = license_hash
    manager.update_settings(payload)


def license_is_current(config_path: str | Path, license_hash: str) -> bool:
    """Return ``True`` when the stored acceptance matches ``license_hash``."""

    manager = ConfigManager(str(config_path))
    accepted = bool(manager.get_setting("license.accepted"))
    accepted_hash = manager.get_setting("license.hash")
    return accepted and accepted_hash == license_hash


def _read_license_text() -> tuple[str, str]:
    license_path = Path(__file__).resolve().parents[4] / "LICENSE"
    try:
        license_text = license_path.read_text(encoding="utf-8")
    except Exception:
        license_text = "License file not found."
    license_hash = sha256(license_text.encode("utf-8")).hexdigest()
    return license_text, license_hash


def _make_card(parent, *, pady=(0, 12)):
    frame = tk.Frame(
        parent,
        bg=PANEL_BG,
        highlightbackground=BORDER,
        highlightcolor=BORDER,
        highlightthickness=1,
        bd=0,
    )
    frame.pack(fill=tk.BOTH, expand=False, padx=14, pady=pady)
    return frame


def show_license_gui(
    config_path: str | Path = "config/pygpt_net/config.json",
    *,
    force_show: bool = False,
) -> bool:
    """Display the license agreement dialog and return ``True`` if shown."""

    if tk is None or scrolledtext is None:
        raise RuntimeError("tkinter is not available")

    license_text, license_hash = _read_license_text()
    current = license_is_current(config_path, license_hash)
    if current and not force_show:
        return False

    view_only = current and force_show

    root = tk.Tk()
    apply_root_chrome(root, title="HueyOS License Center", minsize=(820, 640))

    shell = tk.Frame(root, bg=DARK_BG)
    shell.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    header = _make_card(shell, pady=(0, 10))
    tk.Label(
        header,
        text="HueyOS License Center",
        bg=PANEL_BG,
        fg=LIGHT_FG,
        font=("Segoe UI", 18, "bold"),
        anchor=tk.W,
        justify=tk.LEFT,
    ).pack(fill=tk.X, padx=18, pady=(16, 6))
    tk.Label(
        header,
        text=(
            "Review the current project license before continuing. "
            "This window is also reusable later for manual reference."
        ),
        bg=PANEL_BG,
        fg=MUTED_FG,
        justify=tk.LEFT,
        wraplength=720,
    ).pack(fill=tk.X, padx=18, pady=(0, 8))
    status_text = (
        "This license version is already accepted. Review only."
        if view_only
        else "Acceptance is required before continuing."
    )
    tk.Label(
        header,
        text=status_text,
        bg=ACCENT_PURPLE,
        fg=LIGHT_FG,
        padx=12,
        pady=6,
        anchor=tk.W,
        justify=tk.LEFT,
    ).pack(anchor=tk.W, padx=18, pady=(0, 16))

    content = _make_card(shell)

    text = scrolledtext.ScrolledText(
        content,
        width=100,
        height=25,
        wrap=tk.WORD,
        **text_surface_kwargs(surface="panel_alt"),
    )
    text.insert(tk.END, license_text)
    text.config(state=tk.DISABLED)
    text.pack(fill=tk.BOTH, expand=True, padx=18, pady=(18, 10))

    if view_only:
        tk.Label(
            content,
            text="No action is required. Close this window when you finish reviewing the agreement.",
            bg=PANEL_BG,
            fg=MUTED_FG,
            justify=tk.LEFT,
            wraplength=720,
        ).pack(fill=tk.X, padx=18, pady=(0, 12))

    def on_accept() -> None:
        accept_license(config_path, license_hash)
        if messagebox is not None:
            messagebox.showinfo("License", "License accepted")
            messagebox.showwarning(
                "Experimental",
                "This is experimental software. Proceed with caution.",
            )
        root.destroy()

    def on_decline() -> None:
        if messagebox is not None:
            messagebox.showwarning("License", "You must accept the license to proceed")
        root.destroy()

    btn_frame = tk.Frame(content, bg=PANEL_BG)
    btn_frame.pack(fill=tk.X, padx=18, pady=(0, 18))
    tk.Button(
        btn_frame,
        text="Close" if view_only else "Accept",
        command=root.destroy if view_only else on_accept,
        **primary_button_kwargs(),
    ).pack(side=tk.LEFT, padx=5)
    if not view_only:
        tk.Button(
            btn_frame,
            text="Decline",
            command=on_decline,
            **primary_button_kwargs(),
        ).pack(side=tk.LEFT, padx=5)

    root.mainloop()
    return True


if __name__ == "__main__":
    show_license_gui()


__all__ = [
    "ACCENT_PURPLE",
    "DARK_BG",
    "LIGHT_FG",
    "accept_license",
    "license_is_current",
    "show_license_gui",
]
