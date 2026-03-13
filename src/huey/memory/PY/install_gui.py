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

from .gui_scaling import apply_scaling
from .installer import (
    HARDWARE_OPTIONS,
    SOFTWARE_OPTIONS,
    run_installer,
)
from .license_gui import ACCENT_PURPLE, DARK_BG, LIGHT_FG, accept_license

DEFAULT_CONFIG_PATH = Path("config") / "pygpt_net" / "config.json"


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

    root = tk.Tk()
    apply_scaling(root, os.environ.get("SCREEN_MODE", "1080p"))
    root.title("Monkey Head Project Installer")
    root.minsize(900, 650)
    root.configure(bg=DARK_BG)

    tk.Label(
        root,
        text="Monkey Head Project Installer",
        bg=DARK_BG,
        fg=LIGHT_FG,
        font=("TkDefaultFont", 14, "bold"),
    ).pack(pady=(12, 8))

    controls = tk.Frame(root, bg=DARK_BG)
    controls.pack(fill="x", padx=12)

    tk.Label(controls, text="Hardware:", bg=DARK_BG, fg=LIGHT_FG).grid(
        row=0, column=0, sticky="w", padx=(0, 8), pady=4
    )
    hardware_var = tk.StringVar(value="general")
    hardware_combo = ttk.Combobox(
        controls,
        values=["general", *HARDWARE_OPTIONS],
        textvariable=hardware_var,
        state="readonly",
        width=34,
    )
    hardware_combo.grid(row=0, column=1, sticky="w", pady=4)

    tk.Label(
        controls,
        text="Software packages (Ctrl/⌘ click for multi-select):",
        bg=DARK_BG,
        fg=LIGHT_FG,
    ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 4))

    software_list = tk.Listbox(
        controls,
        selectmode=tk.MULTIPLE,
        width=45,
        height=min(len(SOFTWARE_OPTIONS), 8),
        bg=DARK_BG,
        fg=LIGHT_FG,
        selectbackground=ACCENT_PURPLE,
    )
    for package in SOFTWARE_OPTIONS:
        software_list.insert(tk.END, package)
    software_list.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 8))

    tk.Label(
        root,
        text="License agreement (required):",
        bg=DARK_BG,
        fg=LIGHT_FG,
    ).pack(anchor="w", padx=12)

    license_box = tk.Text(
        root,
        wrap=tk.WORD,
        height=16,
        bg=DARK_BG,
        fg=LIGHT_FG,
        insertbackground=LIGHT_FG,
        highlightbackground=ACCENT_PURPLE,
        highlightcolor=ACCENT_PURPLE,
        highlightthickness=1,
    )
    license_box.insert("1.0", _read_license_text())
    license_box.configure(state=tk.DISABLED)
    license_box.pack(fill="both", expand=True, padx=12, pady=8)

    accepted_var = tk.BooleanVar(value=False)
    tk.Checkbutton(
        root,
        text="I have read and agree to the license terms.",
        variable=accepted_var,
        bg=DARK_BG,
        fg=LIGHT_FG,
        selectcolor=ACCENT_PURPLE,
        activebackground=DARK_BG,
        activeforeground=LIGHT_FG,
    ).pack(anchor="w", padx=12)

    status_var = tk.StringVar(value="Ready")
    tk.Label(root, textvariable=status_var, bg=DARK_BG, fg=LIGHT_FG).pack(
        anchor="w", padx=12, pady=(8, 4)
    )

    progress = ttk.Progressbar(root, mode="indeterminate")
    progress.pack(fill="x", padx=12, pady=(0, 10))

    def _run_install() -> None:
        selected = software_list.curselection()
        software = [SOFTWARE_OPTIONS[idx] for idx in selected] if selected else ["auto"]

        try:
            return_code = run_installer(hardware=hardware_var.get(), software=software)
            if return_code == 0:
                status_var.set("Installation completed successfully.")
                if messagebox is not None:
                    messagebox.showinfo("Install", "Installation completed successfully.")
            else:
                status_var.set(f"Installation failed (code {return_code}).")
                if messagebox is not None:
                    messagebox.showerror("Install", f"Installation failed (code {return_code}).")
        except subprocess.CalledProcessError as exc:
            status_var.set(f"Installation failed (code {exc.returncode}).")
            if messagebox is not None:
                messagebox.showerror("Install", f"Installation failed (code {exc.returncode}).")
        except Exception as exc:  # pragma: no cover - runtime/environment errors
            status_var.set(f"Installation failed: {exc}")
            if messagebox is not None:
                messagebox.showerror("Install", f"Installation failed: {exc}")
        finally:
            progress.stop()
            install_button.configure(state=tk.NORMAL)

    def on_install() -> None:
        try:
            validate_license_acceptance(accepted_var.get())
        except PermissionError:
            if messagebox is not None:
                messagebox.showwarning(
                    "License required",
                    "You must agree to the license before installation.",
                )
            return

        config_path_obj = Path(config_path)
        config_path_obj.parent.mkdir(parents=True, exist_ok=True)
        accept_license(config_path_obj)

        status_var.set("Installing...")
        install_button.configure(state=tk.DISABLED)
        progress.start(10)
        threading.Thread(target=_run_install, daemon=True).start()

    install_button = tk.Button(
        root,
        text="Install",
        command=on_install,
        bg=ACCENT_PURPLE,
        fg=LIGHT_FG,
        activebackground=ACCENT_PURPLE,
        activeforeground=LIGHT_FG,
    )
    install_button.pack(side="left", padx=(12, 4), pady=(0, 14))

    tk.Button(
        root,
        text="Cancel",
        command=root.destroy,
        bg=ACCENT_PURPLE,
        fg=LIGHT_FG,
        activebackground=ACCENT_PURPLE,
        activeforeground=LIGHT_FG,
    ).pack(side="left", padx=4, pady=(0, 14))

    root.mainloop()


__all__ = ["launch_install_gui", "validate_license_acceptance"]
