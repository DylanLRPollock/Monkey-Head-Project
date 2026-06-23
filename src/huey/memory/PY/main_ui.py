# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Main Ui module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
import logging
import os
import threading

os.environ.setdefault("MONKEY_HEAD_LIGHT_IMPORTS", "1")
import platform
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:  # pragma: no cover - optional dependency
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext, simpledialog, ttk
except ImportError:  # pragma: no cover - can't import GUI libs
    tk = None
    messagebox = None
    scrolledtext = None
    filedialog = None
    simpledialog = None
    ttk = None

from huey.config_toggle_gui import run_config_toggle_gui
from huey.gui_scaling import apply_scaling
from huey.license_gui import show_license_gui
from huey.media.media_conversion import convert_media
from huey.memory.PY.ai_tools_gui import run_ai_tools
from huey.memory.PY.dashboard import launch_dashboard
from huey.memory.PY.preload_data import preload_all
from huey.services.container_management import (
    build_docker_image,
    cleanup_images,
    cleanup_kubernetes,
    deploy_kubernetes,
    get_pod_logs,
    manage_containers,
    manage_networks,
    manage_volumes,
    scale_deployment,
    stop_containers,
)
from huey.simple_chat_gui import run_simple_chat

# Dark theme colors
# Updated to use a black background with green text and
# a dark purple accent for frames and windows.
DARK_BG = "#000000"  # black background
LIGHT_FG = "#00ff00"  # green foreground text
ACCENT_PURPLE = "#2d2b57"  # dark purple accent color

logger = logging.getLogger(__name__)


class MainUI:
    def __init__(self, root):
        if tk is None:
            raise RuntimeError("tkinter is not available")

        self.root = root
        self.background_image = None
        self.background_label = None
        mode = self.choose_screen_mode()
        apply_scaling(self.root, mode)
        self.apply_dark_theme()
        self.root.title("Program Manager")
        self.root.minsize(800, 600)
        self.executor = ThreadPoolExecutor(max_workers=os.cpu_count() or 4)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.setup_paths()
        self.create_menu()
        self.create_widgets()
        self.apply_background_image()
        self.check_license()

    def apply_dark_theme(self) -> None:
        """Configure Tk widgets to use a dark purple theme."""
        if tk is None:
            return

        self.root.configure(
            bg=DARK_BG,
            highlightbackground=ACCENT_PURPLE,
            highlightcolor=ACCENT_PURPLE,
            highlightthickness=2,
        )

        if ttk is not None:
            style = ttk.Style(self.root)
            try:
                style.theme_use("clam")
            except (RuntimeError, AttributeError) as e:
                logger.debug(f"Failed to set theme: {e}")
            style.configure("TLabel", background=DARK_BG, foreground=LIGHT_FG)
            style.configure(
                "TButton",
                background=ACCENT_PURPLE,
                foreground=LIGHT_FG,
                relief=tk.RAISED,
            )
            style.map(
                "TButton",
                background=[("active", ACCENT_PURPLE)],
                foreground=[("active", LIGHT_FG)],
            )
            style.configure(
                "TProgressbar",
                troughcolor=DARK_BG,
                background=ACCENT_PURPLE,
            )

    def _find_background_image(self) -> Path | None:
        """Locate the HueyOS background image from the repository root."""
        for parent in Path(__file__).resolve().parents:
            candidate = parent / "HueyOS-background.png"
            if candidate.exists():
                return candidate
        return None

    def apply_background_image(self) -> None:
        """Place the HueyOS background image behind the main window widgets."""
        if tk is None:
            return
        image_path = self._find_background_image()
        if image_path is None:
            return
        try:
            self.background_image = tk.PhotoImage(file=str(image_path))
        except (RuntimeError, AttributeError, OSError) as e:
            logger.debug(f"Failed to load background image: {e}")
            return
        self.background_label = tk.Label(
            self.root, image=self.background_image, bg=DARK_BG
        )
        self.background_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.background_label.lower()

    def choose_screen_mode(self) -> str:
        """Ask the user which display mode to use or read from ``SCREEN_MODE``."""
        env_mode = os.environ.get("SCREEN_MODE")
        if env_mode in {"1080p", "4k", "custom"}:
            return env_mode

        if simpledialog is not None:
            mode = simpledialog.askstring(
                "Display Mode",
                "Choose display mode: 1080p, 4k, or custom",
                initialvalue="1080p",
            )
            if mode and mode.lower() in {"1080p", "4k", "custom"}:
                mode = mode.lower()
                if mode == "custom":
                    if simpledialog is not None:
                        factor = simpledialog.askfloat(
                            "Scaling Factor",
                            "Enter scaling factor",
                            minvalue=0.5,
                            maxvalue=5.0,
                        )
                        if factor is not None:
                            os.environ["SCREEN_FACTOR"] = str(factor)
                        font = simpledialog.askinteger(
                            "Font Size",
                            "Enter base font size",
                            minvalue=6,
                            maxvalue=24,
                        )
                        if font is not None:
                            os.environ["SCREEN_FONT_SIZE"] = str(font)
                return mode
        return "1080p"

    def setup_paths(self):
        """Determine installer paths based on the current platform."""
        root = Path(__file__).resolve().parents[4]
        installers = root / "platform" / "installers"
        memory_dir = root / "src" / "huey" / "memory"
        system = platform.system()
        if system == "Linux":
            debian_installers = installers / "debian" / "Debian"
            self.install_path = debian_installers / "install-deb.sh"
            self.update_path = debian_installers / "update-deb.sh"
            self.run_path = memory_dir / "SH" / "run.sh"
        elif system == "Darwin":
            mac_installers = installers / "macos" / "macOS"
            self.install_path = mac_installers / "install-mac.sh"
            self.update_path = mac_installers / "update-mac.sh"
            self.run_path = memory_dir / "SH" / "run.sh"
        elif system == "Windows":
            windows_installers = installers / "windows" / "Windows"
            self.install_path = windows_installers / "install-win.bat"
            self.update_path = windows_installers / "update-win.bat"
            self.run_path = memory_dir / "BAT" / "run.bat"
        else:
            self.install_path = None
            self.update_path = None
            self.run_path = None

    def create_menu(self):
        menu_bar = tk.Menu(self.root, bg=DARK_BG, fg=LIGHT_FG, tearoff=0)
        self.root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0, bg=DARK_BG, fg=LIGHT_FG)
        file_menu.add_command(label="Install", command=self.install)
        file_menu.add_command(label="Run", command=self.run)
        file_menu.add_command(label="Update", command=self.update)
        file_menu.add_command(label="Clear Log", command=self.clear_log)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

        tools_menu = tk.Menu(menu_bar, tearoff=0, bg=DARK_BG, fg=LIGHT_FG)
        tools_menu.add_command(label="License", command=self.show_license)
        tools_menu.add_command(label="Data Summary", command=self.show_data_summary)
        tools_menu.add_command(label="Convert Media", command=self.convert_media_prompt)
        tools_menu.add_command(label="Config Toggles", command=self.show_config_toggles)
        menu_bar.add_cascade(label="Tools", menu=tools_menu)

        ai_menu = tk.Menu(menu_bar, tearoff=0, bg=DARK_BG, fg=LIGHT_FG)
        ai_menu.add_command(label="Simple Chat", command=self.launch_simple_chat)
        ai_menu.add_command(label="AI Processor Demo", command=self.launch_ai_tools)
        ai_menu.add_command(label="Dashboard", command=self.launch_dashboard)
        menu_bar.add_cascade(label="AI", menu=ai_menu)

        docker_menu = tk.Menu(menu_bar, tearoff=0, bg=DARK_BG, fg=LIGHT_FG)
        docker_menu.add_command(label="Build Image", command=self.build_image)
        docker_menu.add_command(label="Start Containers", command=self.start_containers)
        docker_menu.add_command(label="Stop Containers", command=self.stop_containers)
        docker_menu.add_command(label="Cleanup Images", command=self.cleanup_images)
        docker_menu.add_command(label="Manage Volumes", command=self.manage_volumes)
        docker_menu.add_command(label="Manage Networks", command=self.manage_networks)
        menu_bar.add_cascade(label="Docker", menu=docker_menu)

        k8s_menu = tk.Menu(menu_bar, tearoff=0, bg=DARK_BG, fg=LIGHT_FG)
        k8s_menu.add_command(label="Deploy", command=self.deploy_kubernetes)
        k8s_menu.add_command(
            label="Scale Deployment", command=self.scale_deployment_prompt
        )
        k8s_menu.add_command(label="Get Pod Logs", command=self.get_pod_logs_prompt)
        k8s_menu.add_command(label="Cleanup", command=self.cleanup_kubernetes)
        menu_bar.add_cascade(label="Kubernetes", menu=k8s_menu)

    def create_widgets(self):
        main_frame = tk.Frame(self.root, bg=DARK_BG)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        self.log_text = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            bg=DARK_BG,
            fg=LIGHT_FG,
            insertbackground=LIGHT_FG,
            highlightbackground=ACCENT_PURPLE,
            highlightcolor=ACCENT_PURPLE,
            highlightthickness=2,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.progress = ttk.Progressbar(
            main_frame, orient=tk.HORIZONTAL, mode="indeterminate"
        )
        self.progress.pack(fill=tk.X, pady=(10, 0))

        button_frame = tk.Frame(main_frame, bg=DARK_BG)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        self.status_label = tk.Label(
            self.root,
            text="Status: Ready",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg=DARK_BG,
            fg=LIGHT_FG,
            highlightbackground=ACCENT_PURPLE,
            highlightcolor=ACCENT_PURPLE,
            highlightthickness=2,
        )
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM, ipady=2)

        self.install_button = tk.Button(
            button_frame,
            text="Install",
            command=self.install,
            bg=ACCENT_PURPLE,
            fg=LIGHT_FG,
            activebackground=ACCENT_PURPLE,
            activeforeground=LIGHT_FG,
        )
        self.install_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.run_button = tk.Button(
            button_frame,
            text="Run",
            command=self.run,
            bg=ACCENT_PURPLE,
            fg=LIGHT_FG,
            activebackground=ACCENT_PURPLE,
            activeforeground=LIGHT_FG,
        )
        self.run_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.update_button = tk.Button(
            button_frame,
            text="Update",
            command=self.update,
            bg=ACCENT_PURPLE,
            fg=LIGHT_FG,
            activebackground=ACCENT_PURPLE,
            activeforeground=LIGHT_FG,
        )
        self.update_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.clear_button = tk.Button(
            button_frame,
            text="Clear Log",
            command=self.clear_log,
            bg=ACCENT_PURPLE,
            fg=LIGHT_FG,
            activebackground=ACCENT_PURPLE,
            activeforeground=LIGHT_FG,
        )
        self.clear_button.pack(side=tk.LEFT, padx=10, pady=10)

    def _run_on_ui(self, callback: Callable[[], None]) -> None:
        """Schedule ``callback`` on Tk's UI thread when possible."""

        root = getattr(self, "root", None)
        if root is not None and hasattr(root, "after"):
            root.after(0, callback)
        else:
            callback()

    def _set_status(self, text: str) -> None:
        self._run_on_ui(lambda: self.status_label.config(text=text))

    def _start_progress(self) -> None:
        self._run_on_ui(lambda: self.progress.start())

    def _stop_progress(self) -> None:
        self._run_on_ui(lambda: self.progress.stop())

    def log_message(self, message):
        def append() -> None:
            self.log_text.insert(tk.END, str(message).rstrip() + "\n")
            self.log_text.see(tk.END)

        self._run_on_ui(append)

    def clear_log(self) -> None:
        """Remove all text from the log window."""
        self.log_text.delete("1.0", tk.END)

    def run_script(self, script_path):
        if script_path is None or not Path(script_path).exists():
            self.log_message(f"Script not found: {script_path}")
            if messagebox is not None:
                self._run_on_ui(
                    lambda: messagebox.showerror(
                        "Error", "Installer script not found for this platform."
                    )
                )
            self._stop_progress()
            self._set_status("Status: Ready")
            return
        try:
            if str(script_path).endswith(".bat"):
                cmd = ["cmd", "/c", str(script_path)]
            else:
                cmd = ["bash", str(script_path)]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if process.stdout is not None:
                for line in process.stdout:
                    self.log_message(line)
                process.stdout.close()
            process.wait()
            if process.returncode != 0:
                self.log_message(f"Error: command exited with {process.returncode}")
            else:
                self.log_message("Operation completed successfully.")
        except Exception as e:
            self.log_message(f"Exception: {str(e)}")
        finally:
            self._stop_progress()
            self._set_status("Status: Ready")

    def install(self):
        self.log_message("Starting installation...")
        self._set_status("Status: Installing")
        self._start_progress()
        self._submit_task(self.run_script, self.install_path)

    def run(self):
        self.log_message("Launching application...")
        self._set_status("Status: Running")
        self._start_progress()
        self._submit_task(self.run_script, self.run_path)

    def update(self):
        self.log_message("Starting update...")
        self._set_status("Status: Updating")
        self._start_progress()
        self._submit_task(self.run_script, self.update_path)

    def check_license(self):
        """Display the license agreement if not yet accepted."""
        show_license_gui()

    def show_license(self):
        """Manually open the license dialog."""
        show_license_gui()

    def show_data_summary(self):
        """Display counts of bundled prompts and memory files."""
        data = preload_all()
        prompts = len(data.get("prompts", []))
        memory_files = sum(len(v) for v in data.get("memory", {}).values())
        messagebox.showinfo(
            "Data Summary", f"Prompts: {prompts}\nMemory files: {memory_files}"
        )

    def show_config_toggles(self):
        """Open the configuration toggles window in a thread."""
        self.log_message("Opening config toggles...")
        self._launch_child_gui(run_config_toggle_gui, "Config Toggles")

    def _run_container_func(self, func, *args):
        try:
            func(*args)
            self.log_message("Operation completed successfully.")
        except Exception as exc:  # pragma: no cover - subprocess failures
            self.log_message(f"Exception: {exc}")
        finally:
            self._stop_progress()
            self._set_status("Status: Ready")

    def _submit_task(self, func, *args):
        executor = getattr(self, "executor", None)
        if executor is not None:
            executor.submit(func, *args)
        else:  # fallback for tests
            threading.Thread(target=func, args=args).start()

    def build_image(self):
        self.log_message("Building Docker image...")
        self._set_status("Status: Building")
        self._start_progress()
        self._submit_task(self._run_container_func, build_docker_image)

    def start_containers(self):
        self.log_message("Starting containers...")
        self._set_status("Status: Starting")
        self._start_progress()
        self._submit_task(self._run_container_func, manage_containers)

    def stop_containers(self):
        self.log_message("Stopping containers...")
        self._set_status("Status: Stopping")
        self._start_progress()
        self._submit_task(self._run_container_func, stop_containers)

    def cleanup_images(self):
        self.log_message("Pruning images...")
        self._set_status("Status: Cleaning")
        self._start_progress()
        self._submit_task(self._run_container_func, cleanup_images)

    def manage_volumes(self):
        self.log_message("Managing volumes...")
        self._set_status("Status: Volumes")
        self._start_progress()
        self._submit_task(self._run_container_func, manage_volumes)

    def manage_networks(self):
        self.log_message("Managing networks...")
        self._set_status("Status: Networks")
        self._start_progress()
        self._submit_task(self._run_container_func, manage_networks)

    def deploy_kubernetes(self):
        self.log_message("Deploying Kubernetes resources...")
        self._set_status("Status: Deploying")
        self._start_progress()
        self._submit_task(self._run_container_func, deploy_kubernetes)

    def cleanup_kubernetes(self):
        self.log_message("Cleaning Kubernetes resources...")
        self._set_status("Status: Cleaning")
        self._start_progress()
        self._submit_task(self._run_container_func, cleanup_kubernetes)

    def scale_deployment_prompt(self):
        name = simpledialog.askstring("Deployment", "Deployment name:")
        if not name:
            return
        replicas = simpledialog.askinteger("Replicas", "Number of replicas:")
        if replicas is None:
            return
        self.log_message(f"Scaling {name} to {replicas}...")
        self._set_status("Status: Scaling")
        self._start_progress()
        self._submit_task(self._run_container_func, scale_deployment, name, replicas)

    def get_pod_logs_prompt(self):
        pod = simpledialog.askstring("Pod", "Pod name:")
        if not pod:
            return
        self.log_message(f"Fetching logs for {pod}...")
        self._set_status("Status: Logs")
        self._start_progress()
        self._submit_task(self._get_logs, pod)

    def convert_media_prompt(self):
        if filedialog is None:
            messagebox.showerror("Error", "Tkinter is not available")
            return
        src = filedialog.askopenfilename(title="Select source file")
        if not src:
            return
        dst = filedialog.asksaveasfilename(title="Select output file")
        if not dst:
            return
        bitrate = simpledialog.askstring(
            "Audio Bitrate", "Bitrate", initialvalue="192k"
        )
        codec = simpledialog.askstring("Video Codec", "Codec", initialvalue="libx264")
        self.log_message(f"Converting {src} -> {dst}...")
        self._set_status("Status: Converting")
        self._start_progress()
        self._submit_task(self._convert_media_thread, src, dst, bitrate, codec)

    def _convert_media_thread(self, src, dst, bitrate, codec):
        try:
            convert_media(src, dst, bitrate=bitrate, codec=codec)
            self.log_message("Operation completed successfully.")
        except Exception as exc:  # pragma: no cover - ffmpeg errors
            self.log_message(f"Exception: {exc}")
        finally:
            self._stop_progress()
            self._set_status("Status: Ready")

    def _get_logs(self, pod):
        try:
            logs = get_pod_logs(pod)
            self.log_message(logs)
            self.log_message("Operation completed successfully.")
        except Exception as exc:  # pragma: no cover - subprocess failures
            self.log_message(f"Exception: {exc}")
        finally:
            self._stop_progress()
            self._set_status("Status: Ready")

    def _launch_child_gui(self, func, label: str) -> None:
        """Open another GUI from Tk's UI thread and report launch errors."""

        def launch() -> None:
            try:
                func()
            except Exception as exc:  # pragma: no cover - GUI dependency failures
                self.log_message(f"{label} failed: {exc}")
                if messagebox is not None:
                    messagebox.showerror(label, str(exc))

        self._run_on_ui(launch)

    def launch_simple_chat(self):
        """Open the simple chat demo."""
        self.log_message("Launching simple chat demo...")
        self._launch_child_gui(run_simple_chat, "Simple Chat")

    def launch_ai_tools(self):
        """Open the AI tools window."""
        self.log_message("Launching AI tools...")
        self._launch_child_gui(run_ai_tools, "AI Tools")

    def launch_dashboard(self):
        """Open the PySide dashboard."""
        self.log_message("Launching dashboard...")
        try:
            launch_dashboard()
        except RuntimeError as exc:
            messagebox.showerror("Dashboard", str(exc))

    def on_close(self):
        """Shutdown the executor and close the UI."""
        if hasattr(self, "executor"):
            self.executor.shutdown(wait=False)
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = MainUI(root)
    root.mainloop()
