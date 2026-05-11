# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Ai Tools Gui module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.12.2025
# ==================================================
"""Feature rich Tkinter console for :class:`AIProcessor` and system tooling."""

from __future__ import annotations

import logging
import os
import threading

try:  # pragma: no cover - optional dependency
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext, ttk
except Exception:  # pragma: no cover - can't import GUI libs
    tk = None
    messagebox = None
    filedialog = None
    scrolledtext = None
    ttk = None

from .gui_scaling import apply_scaling
from .license_gui import ACCENT_PURPLE, DARK_BG, LIGHT_FG

try:  # pragma: no cover - psutil optional dependency
    import psutil  # type: ignore
except Exception:  # pragma: no cover - psutil missing at runtime
    psutil = None  # type: ignore[assignment]

import platform
import shutil
import socket
import time
from pathlib import Path
from typing import Dict, List

from huey.memory.PY.llm import LLMAdapter, LLMProvider
from huey.utils.paths import ensure_subdirectory, get_memory_path

from .config_manager import ConfigManager

logger = logging.getLogger(__name__)


def _format_bytes(size: float | int | None) -> str:
    """Return ``size`` formatted as a human readable string."""

    if size is None:
        return "Unknown"
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size)
    for unit in units:
        if size < 1024.0:
            return f"{size:0.2f} {unit}"
        size /= 1024.0
    return f"{size:0.2f} PB"


def _gather_system_status() -> Dict[str, str]:
    """Collect system metrics for display in the GUI."""

    uname = platform.uname()
    data: Dict[str, str] = {
        "hostname": socket.gethostname(),
        "system": uname.system,
        "release": uname.release,
        "python": platform.python_version(),
    }

    if psutil is not None:  # pragma: no branch - determined at import time
        try:
            data["cpu"] = f"{psutil.cpu_percent(interval=0.05):0.1f}%"
        except Exception:
            data["cpu"] = "Unavailable"
        try:
            virtual = psutil.virtual_memory()
            data["memory"] = (
                f"{_format_bytes(virtual.used)} used / {_format_bytes(virtual.total)}"
            )
            if virtual.total:
                percent = (virtual.used / virtual.total) * 100
                data["memory_percent"] = f"{percent:0.1f}"
        except Exception:
            data["memory"] = "Unavailable"
        try:
            boot_time = getattr(psutil, "boot_time", lambda: None)()
        except Exception:
            boot_time = None
        if boot_time:
            uptime = max(0.0, time.time() - float(boot_time))
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            data["uptime"] = f"{hours}h {minutes}m"
    else:
        data["cpu"] = "psutil not installed"
        data["memory"] = "psutil not installed"

    try:
        disk = shutil.disk_usage(Path("/"))
        data["disk"] = f"{_format_bytes(disk.used)} used / {_format_bytes(disk.total)}"
    except Exception:
        data["disk"] = "Unavailable"

    memory_dir = get_memory_path(create=True)
    data["memory_path"] = str(memory_dir)
    try:
        total_size = 0
        for entry in memory_dir.rglob("*"):
            if entry.is_file():
                total_size += entry.stat().st_size
        data["memory_dir_size"] = _format_bytes(total_size)
    except Exception:
        data["memory_dir_size"] = "Unavailable"

    return data


def _list_memory_uploads(target_dir: Path) -> List[str]:
    """Return a list of uploaded files inside ``target_dir``."""

    items: List[str] = []
    try:
        for entry in sorted(target_dir.glob("**/*")):
            if entry.is_file():
                relative = entry.relative_to(target_dir)
                items.append(f"{relative} ({_format_bytes(entry.stat().st_size)})")
    except Exception:
        items = ["Unable to read uploads directory"]
    if not items:
        items.append("No uploaded files yet")
    return items


def run_ai_tools() -> None:
    """Launch an enhanced GUI exposing system insights and AI helpers."""

    if tk is None or messagebox is None or ttk is None or scrolledtext is None:
        raise RuntimeError("tkinter is not available")

    from .ai_processor import AIProcessor  # pragma: no cover - optional

    proc = AIProcessor()
    config = ConfigManager("config/pygpt_net/config.json")
    uploads_dir = ensure_subdirectory("GUI", "uploads")

    root = tk.Tk()
    apply_scaling(root, os.environ.get("SCREEN_MODE", "1080p"))
    root.title("AI Tools Console")
    root.configure(bg=DARK_BG)

    style = ttk.Style(root)
    style_errors: tuple[type[BaseException], ...] = (
        RuntimeError,
        AttributeError,
        ValueError,
        TypeError,
    )
    if tk is not None and hasattr(tk, "TclError"):
        style_errors = (*style_errors, tk.TclError)
    try:
        style.theme_use("clam")
    except style_errors as exc:
        logger.debug("Unable to apply ttk theme 'clam': %s", exc)
    style.configure("TNotebook", background=DARK_BG)
    style.configure("TNotebook.Tab", background=ACCENT_PURPLE, foreground=LIGHT_FG)
    style.map(
        "TNotebook.Tab",
        background=[("selected", DARK_BG)],
        foreground=[("selected", LIGHT_FG)],
    )

    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # ------------------------------------------------------------------
    # Processing tab
    # ------------------------------------------------------------------
    process_frame = tk.Frame(notebook, bg=DARK_BG)
    notebook.add(process_frame, text="Processing")

    tk.Label(process_frame, text="Input Text", bg=DARK_BG, fg=LIGHT_FG).pack(
        padx=5, pady=(5, 2), anchor=tk.W
    )
    text_entry = tk.Entry(
        process_frame, width=60, bg=DARK_BG, fg=LIGHT_FG, insertbackground=LIGHT_FG
    )
    text_entry.pack(padx=5, pady=2, fill=tk.X)

    def on_process() -> None:
        text = text_entry.get()
        result = proc.process_data(text)
        messagebox.showinfo("Processed", result)

    tk.Button(
        process_frame,
        text="Process",
        command=on_process,
        bg=ACCENT_PURPLE,
        fg=LIGHT_FG,
    ).pack(pady=5, anchor=tk.E, padx=5)

    tk.Label(
        process_frame,
        text="Numbers (comma separated)",
        bg=DARK_BG,
        fg=LIGHT_FG,
    ).pack(padx=5, pady=(15, 2), anchor=tk.W)
    num_entry = tk.Entry(
        process_frame, width=60, bg=DARK_BG, fg=LIGHT_FG, insertbackground=LIGHT_FG
    )
    num_entry.pack(padx=5, pady=2, fill=tk.X)

    def on_mean() -> None:
        raw = num_entry.get()
        try:
            nums = [float(x.strip()) for x in raw.split(",") if x.strip()]
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers")
            return
        result = proc.compute_mean(nums) if nums else 0.0
        messagebox.showinfo("Mean", f"{result:0.4f}")

    tk.Button(
        process_frame,
        text="Compute Mean",
        command=on_mean,
        bg=ACCENT_PURPLE,
        fg=LIGHT_FG,
    ).pack(pady=5, anchor=tk.E, padx=5)

    # ------------------------------------------------------------------
    # System tab
    # ------------------------------------------------------------------
    system_frame = tk.Frame(notebook, bg=DARK_BG)
    notebook.add(system_frame, text="System Status")

    status_vars: Dict[str, tk.StringVar] = {
        "hostname": tk.StringVar(value=""),
        "system": tk.StringVar(value=""),
        "release": tk.StringVar(value=""),
        "python": tk.StringVar(value=""),
        "cpu": tk.StringVar(value=""),
        "memory": tk.StringVar(value=""),
        "disk": tk.StringVar(value=""),
        "uptime": tk.StringVar(value=""),
        "memory_path": tk.StringVar(value=""),
        "memory_dir_size": tk.StringVar(value=""),
    }

    for row, (label, var) in enumerate(status_vars.items()):
        tk.Label(
            system_frame,
            text=label.title().replace("_", " "),
            bg=DARK_BG,
            fg=LIGHT_FG,
        ).grid(row=row, column=0, sticky=tk.W, padx=10, pady=3)
        tk.Label(system_frame, textvariable=var, bg=DARK_BG, fg=LIGHT_FG).grid(
            row=row, column=1, sticky=tk.W, padx=10, pady=3
        )

    mem_progress = ttk.Progressbar(system_frame, length=250)
    mem_progress.grid(row=5, column=2, padx=10, pady=3, sticky=tk.W)

    def refresh_system() -> None:
        status = _gather_system_status()
        for key, var in status_vars.items():
            var.set(status.get(key, ""))
        percent = status.get("memory_percent")
        try:
            mem_progress.configure(value=float(percent))
        except Exception:
            mem_progress.configure(value=0)

    ttk.Button(
        system_frame,
        text="Refresh",
        command=refresh_system,
    ).grid(row=len(status_vars), column=0, columnspan=2, padx=10, pady=10, sticky=tk.W)

    refresh_system()

    # ------------------------------------------------------------------
    # Memory tab
    # ------------------------------------------------------------------
    memory_frame = tk.Frame(notebook, bg=DARK_BG)
    notebook.add(memory_frame, text="Memory")

    tk.Label(
        memory_frame,
        text=f"Uploads directory: {uploads_dir}",
        bg=DARK_BG,
        fg=LIGHT_FG,
        wraplength=500,
        justify=tk.LEFT,
    ).pack(padx=10, pady=(10, 5), anchor=tk.W)

    uploads_list = tk.Listbox(
        memory_frame, width=70, height=10, bg=DARK_BG, fg=LIGHT_FG
    )
    uploads_list.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

    def populate_uploads() -> None:
        uploads_list.delete(0, tk.END)
        for item in _list_memory_uploads(uploads_dir):
            uploads_list.insert(tk.END, item)

    def on_upload() -> None:
        if filedialog is None:
            messagebox.showerror("File Upload", "File dialog not available")
            return
        filenames = filedialog.askopenfilenames(title="Select files to upload")
        if not filenames:
            return
        for name in filenames:
            src = Path(name)
            if not src.exists():
                continue
            destination = uploads_dir / src.name
            try:
                shutil.copy2(src, destination)
            except Exception as exc:
                messagebox.showerror("Upload failed", str(exc))
                return
        messagebox.showinfo("Upload", "Files uploaded to memory")
        populate_uploads()

    def on_open_memory() -> None:
        path = get_memory_path(create=True)
        messagebox.showinfo("Memory Path", str(path))

    btn_frame = tk.Frame(memory_frame, bg=DARK_BG)
    btn_frame.pack(pady=5)
    tk.Button(
        btn_frame,
        text="Upload Files",
        command=on_upload,
        bg=ACCENT_PURPLE,
        fg=LIGHT_FG,
    ).pack(side=tk.LEFT, padx=5)
    tk.Button(
        btn_frame,
        text="Open Memory Path",
        command=on_open_memory,
        bg=ACCENT_PURPLE,
        fg=LIGHT_FG,
    ).pack(side=tk.LEFT, padx=5)
    tk.Button(
        btn_frame,
        text="Refresh",
        command=populate_uploads,
        bg=ACCENT_PURPLE,
        fg=LIGHT_FG,
    ).pack(side=tk.LEFT, padx=5)

    populate_uploads()

    # ------------------------------------------------------------------
    # LLM tab
    # ------------------------------------------------------------------
    llm_frame = tk.Frame(notebook, bg=DARK_BG)
    notebook.add(llm_frame, text="LLM Console")

    tk.Label(llm_frame, text="Provider", bg=DARK_BG, fg=LIGHT_FG).grid(
        row=0, column=0, padx=10, pady=5, sticky=tk.W
    )

    default_provider = config.get_setting(
        "agent.llama.provider", LLMProvider.OPENAI.value
    )
    try:
        default_provider = LLMProvider(default_provider).value
    except ValueError:
        default_provider = LLMProvider.OPENAI.value

    provider_var = tk.StringVar(value=default_provider)
    provider_menu = ttk.Combobox(
        llm_frame,
        textvariable=provider_var,
        values=[provider.value for provider in LLMProvider],
        state="readonly",
    )
    provider_menu.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)

    tk.Label(llm_frame, text="Model", bg=DARK_BG, fg=LIGHT_FG).grid(
        row=0, column=2, padx=10, pady=5, sticky=tk.W
    )
    model_var = tk.StringVar(
        value=config.get_setting("agent.llama.model", "gpt-4o-mini") or "gpt-4o-mini"
    )
    tk.Entry(
        llm_frame,
        textvariable=model_var,
        bg=DARK_BG,
        fg=LIGHT_FG,
        insertbackground=LIGHT_FG,
    ).grid(row=0, column=3, padx=10, pady=5, sticky=tk.W)

    chat_display = scrolledtext.ScrolledText(
        llm_frame,
        width=80,
        height=15,
        bg=DARK_BG,
        fg=LIGHT_FG,
        state=tk.DISABLED,
        insertbackground=LIGHT_FG,
    )
    chat_display.grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

    llm_frame.grid_rowconfigure(1, weight=1)
    llm_frame.grid_columnconfigure(0, weight=1)
    llm_frame.grid_columnconfigure(1, weight=0)
    llm_frame.grid_columnconfigure(2, weight=0)
    llm_frame.grid_columnconfigure(3, weight=1)

    input_var = tk.StringVar()
    input_entry = tk.Entry(
        llm_frame,
        textvariable=input_var,
        bg=DARK_BG,
        fg=LIGHT_FG,
        insertbackground=LIGHT_FG,
    )
    input_entry.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
    input_entry.bind("<Return>", lambda event: on_send())

    conversation: List[Dict[str, str]] = []

    def append_chat(prefix: str, text: str) -> None:
        chat_display.configure(state=tk.NORMAL)
        chat_display.insert(tk.END, f"{prefix}: {text}\n")
        chat_display.configure(state=tk.DISABLED)
        chat_display.see(tk.END)

    def on_send() -> None:
        message = input_var.get().strip()
        if not message:
            return
        input_var.set("")
        append_chat("You", message)
        conversation.append({"role": "user", "content": message})
        send_button.configure(state=tk.DISABLED)
        provider_value = provider_var.get()
        model_value = model_var.get() or "gpt-4o-mini"
        try:
            provider = LLMProvider(provider_value)
        except ValueError:
            provider = LLMProvider.OPENAI
        settings = config.get_setting(f"llm.{provider.value}.settings", {})
        if not isinstance(settings, dict):
            settings = {}
        messages = list(conversation)

        def generate_response() -> None:
            try:
                adapter = LLMAdapter(
                    provider,
                    model=model_value,
                    settings=settings,
                )
                response = adapter.generate(prompt=message, messages=messages)
            except Exception as exc:  # pragma: no cover - depends on optional libs
                response = f"Failed to reach provider: {exc}"

            def finish() -> None:
                conversation.append({"role": "assistant", "content": response})
                append_chat(provider.value, response)
                send_button.configure(state=tk.NORMAL)

            root.after(0, finish)

        threading.Thread(target=generate_response, daemon=True).start()

    def on_clear() -> None:
        conversation.clear()
        chat_display.configure(state=tk.NORMAL)
        chat_display.delete("1.0", tk.END)
        chat_display.configure(state=tk.DISABLED)

    send_button = tk.Button(
        llm_frame,
        text="Send",
        command=on_send,
        bg=ACCENT_PURPLE,
        fg=LIGHT_FG,
    )
    send_button.grid(row=2, column=3, padx=10, pady=5, sticky=tk.E)
    tk.Button(
        llm_frame,
        text="Clear",
        command=on_clear,
        bg=ACCENT_PURPLE,
        fg=LIGHT_FG,
    ).grid(row=3, column=3, padx=10, pady=(0, 10), sticky=tk.E)

    notebook.select(process_frame)

    root.mainloop()


__all__ = ["run_ai_tools"]
