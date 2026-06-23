# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Install Gui module (huey/memory/PY)

from __future__ import annotations

import os
import subprocess
import threading
from pathlib import Path

try:  # pragma: no cover - optional dependency
    import tkinter as tk
    from tkinter import messagebox, ttk
except Exception:  # pragma: no cover - can't import GUI libs
    tk = None
    messagebox = None
    ttk = None

from huey.gui.tk import (
    apply_root_chrome,
    apply_ttk_chrome,
    listbox_kwargs,
    primary_button_kwargs,
    text_surface_kwargs,
    tk_palette,
)

from .installer import (
    HARDWARE_OPTIONS,
    SOFTWARE_OPTIONS,
    run_installer,
)
from .license_gui import accept_license, show_license_gui

DEFAULT_CONFIG_PATH = Path("config") / "pygpt_net" / "config.json"

_PALETTE = tk_palette()
DARK_BG = _PALETTE["background"]
PANEL_BG = _PALETTE["panel"]
LIGHT_FG = _PALETTE["text"]
MUTED_FG = _PALETTE["muted_text"]
BORDER = _PALETTE["border"]


def _make_card(parent, *, pady=(0, 12)):
    frame = tk.Frame(
        parent,
        bg=PANEL_BG,
        highlightbackground=BORDER,
        highlightcolor=BORDER,
        highlightthickness=1,
        bd=0,
    )
    frame.pack(fill="both", expand=False, padx=12, pady=pady)
    return frame


def _read_license_text() -> str:
    license_path = Path(__file__).resolve().parents[4] / "LICENSE"
    try:
        return license_path.read_text(encoding="utf-8")
    except Exception:
        return "License file not found."


def validate_license_acceptance(accepted: bool) -> None:
    """Ensure license terms were accepted before installation continues."""

    if not accepted:
        raise PermissionError("License must be accepted before installation")


def launch_install_gui(config_path: str | Path = DEFAULT_CONFIG_PATH) -> None:
    """Launch a graphical installer with explicit license agreement."""

    if tk is None or ttk is None:
        raise RuntimeError("tkinter is not available")

    config_path_obj = Path(config_path)
    root = tk.Tk()
    apply_root_chrome(
        root,
        title="HueyOS Graphical Installer",
        minsize=(920, 680),
        screen_mode=os.environ.get("SCREEN_MODE", "1080p"),
    )
    apply_ttk_chrome(root, ttk)

    shell = tk.Frame(root, bg=DARK_BG)
    shell.pack(fill="both", expand=True, padx=10, pady=10)

    header = _make_card(shell, pady=(0, 10))
    tk.Label(
        header,
        text="HueyOS Graphical Installer",
        bg=PANEL_BG,
        fg=LIGHT_FG,
        font=("Segoe UI", 18, "bold"),
        anchor="w",
        justify="left",
    ).pack(fill="x", padx=18, pady=(16, 6))
    tk.Label(
        header,
        text=(
            "Pick the target hardware profile, choose the software packages you "
            "want, confirm the license, and run installation without leaving the "
            "HueyOS GUI flow."
        ),
        bg=PANEL_BG,
        fg=MUTED_FG,
        justify="left",
        wraplength=780,
    ).pack(fill="x", padx=18, pady=(0, 8))
    tk.Label(
        header,
        text="Review -> Select -> Accept -> Install",
        bg=_PALETTE["accent"],
        fg=LIGHT_FG,
        padx=12,
        pady=6,
        anchor="w",
        justify="left",
    ).pack(anchor="w", padx=18, pady=(0, 16))

    controls = _make_card(shell)
    tk.Label(
        controls,
        text="Install target",
        bg=PANEL_BG,
        fg=LIGHT_FG,
        font=("Segoe UI", 13, "bold"),
        anchor="w",
        justify="left",
    ).grid(row=0, column=0, columnspan=2, sticky="w", padx=18, pady=(16, 6))
    tk.Label(
        controls,
        text="Choose the destination profile and software bundle before running the installer.",
        bg=PANEL_BG,
        fg=MUTED_FG,
        justify="left",
        wraplength=740,
    ).grid(row=1, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 12))

    tk.Label(controls, text="Hardware:", bg=PANEL_BG, fg=LIGHT_FG).grid(
        row=2, column=0, sticky="w", padx=(18, 8), pady=4
    )
    hardware_var = tk.StringVar(value="general")
    hardware_combo = ttk.Combobox(
        controls,
        values=["general", *HARDWARE_OPTIONS],
        textvariable=hardware_var,
        state="readonly",
        width=34,
    )
    hardware_combo.grid(row=2, column=1, sticky="w", pady=4, padx=(0, 18))

    tk.Label(
        controls,
        text="Software packages (Ctrl/Cmd click for multi-select):",
        bg=PANEL_BG,
        fg=LIGHT_FG,
    ).grid(row=3, column=0, columnspan=2, sticky="w", padx=18, pady=(8, 4))

    software_list = tk.Listbox(
        controls,
        selectmode=tk.MULTIPLE,
        width=45,
        height=max(1, min(len(SOFTWARE_OPTIONS), 8)),
        **listbox_kwargs(),
    )
    for package in SOFTWARE_OPTIONS:
        software_list.insert(tk.END, package)
    software_list.grid(row=4, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 18))

    license_card = _make_card(shell)
    tk.Label(
        license_card,
        text="License agreement",
        bg=PANEL_BG,
        fg=LIGHT_FG,
        font=("Segoe UI", 13, "bold"),
        anchor="w",
        justify="left",
    ).pack(fill="x", padx=18, pady=(16, 6))
    tk.Label(
        license_card,
        text="Read the current agreement below. Acceptance is required before installation starts.",
        bg=PANEL_BG,
        fg=MUTED_FG,
        justify="left",
        wraplength=780,
    ).pack(fill="x", padx=18, pady=(0, 12))

    license_box = tk.Text(
        license_card,
        wrap=tk.WORD,
        height=16,
        **text_surface_kwargs(surface="panel_alt"),
    )
    license_box.insert("1.0", _read_license_text())
    license_box.configure(state=tk.DISABLED)
    license_box.pack(fill="both", expand=True, padx=18, pady=(0, 10))

    accepted_var = tk.BooleanVar(value=False)
    tk.Checkbutton(
        license_card,
        text="I have read and agree to the license terms.",
        variable=accepted_var,
        bg=PANEL_BG,
        fg=LIGHT_FG,
        selectcolor=_PALETTE["accent"],
        activebackground=PANEL_BG,
        activeforeground=LIGHT_FG,
    ).pack(anchor="w", padx=18, pady=(0, 10))

    tk.Button(
        license_card,
        text="Open standalone license review",
        command=lambda: show_license_gui(config_path_obj, force_show=True),
        **primary_button_kwargs(),
    ).pack(anchor="w", padx=18, pady=(0, 18))

    status_var = tk.StringVar(value="Ready")
    footer = _make_card(shell, pady=(0, 0))
    tk.Label(
        footer,
        text="Install status",
        bg=PANEL_BG,
        fg=LIGHT_FG,
        font=("Segoe UI", 13, "bold"),
        anchor="w",
        justify="left",
    ).pack(fill="x", padx=18, pady=(16, 6))
    tk.Label(
        footer,
        text="The installer runs on a background thread so this window stays responsive while progress updates.",
        bg=PANEL_BG,
        fg=MUTED_FG,
        justify="left",
        wraplength=780,
    ).pack(fill="x", padx=18, pady=(0, 10))
    tk.Label(footer, textvariable=status_var, bg=PANEL_BG, fg=LIGHT_FG).pack(
        anchor="w", padx=18, pady=(0, 4)
    )
    progress = ttk.Progressbar(footer, mode="indeterminate")
    progress.pack(fill="x", padx=18, pady=(0, 12))

    def _ui(callback) -> None:
        root.after(0, callback)

    def _show_message(kind: str, title: str, text: str) -> None:
        if messagebox is None:
            return
        if kind == "info":
            messagebox.showinfo(title, text)
        elif kind == "warning":
            messagebox.showwarning(title, text)
        else:
            messagebox.showerror(title, text)

    def _run_install(hardware: str, software: list[str]) -> None:
        try:
            return_code = run_installer(hardware=hardware, software=software)
            if return_code == 0:
                _ui(lambda: status_var.set("Installation completed successfully."))
                _ui(
                    lambda: _show_message(
                        "info",
                        "Install",
                        "Installation completed successfully.",
                    )
                )
            else:
                text = f"Installation failed (code {return_code})."
                _ui(lambda: status_var.set(text))
                _ui(lambda: _show_message("error", "Install", text))
        except subprocess.CalledProcessError as exc:
            text = f"Installation failed (code {exc.returncode})."
            _ui(lambda: status_var.set(text))
            _ui(lambda: _show_message("error", "Install", text))
        except Exception as exc:  # pragma: no cover - runtime/environment errors
            text = f"Installation failed: {exc}"
            _ui(lambda: status_var.set(text))
            _ui(lambda: _show_message("error", "Install", text))
        finally:
            _ui(progress.stop)
            _ui(lambda: install_button.configure(state=tk.NORMAL))

    def on_install() -> None:
        try:
            validate_license_acceptance(accepted_var.get())
        except PermissionError:
            _show_message(
                "warning",
                "License required",
                "You must agree to the license before installation.",
            )
            return

        config_path_obj.parent.mkdir(parents=True, exist_ok=True)
        accept_license(config_path_obj)

        selected = software_list.curselection()
        software = [SOFTWARE_OPTIONS[idx] for idx in selected] if selected else ["auto"]
        hardware = hardware_var.get()
        status_var.set("Installing...")
        install_button.configure(state=tk.DISABLED)
        progress.start(10)
        threading.Thread(
            target=_run_install,
            args=(hardware, software),
            daemon=True,
        ).start()

    button_row = tk.Frame(footer, bg=PANEL_BG)
    button_row.pack(fill="x", padx=18, pady=(0, 18))
    install_button = tk.Button(
        button_row,
        text="Install",
        command=on_install,
        **primary_button_kwargs(),
    )
    install_button.pack(side="left", padx=(0, 6))

    tk.Button(
        button_row,
        text="Cancel",
        command=root.destroy,
        **primary_button_kwargs(),
    ).pack(side="left", padx=6)

    root.mainloop()


__all__ = ["launch_install_gui", "validate_license_acceptance"]
