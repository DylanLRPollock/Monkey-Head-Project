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
import os
import threading

os.environ.setdefault("MONKEY_HEAD_LIGHT_IMPORTS", "1")
import platform
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:  # pragma: no cover - optional dependency
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext, simpledialog, ttk
except Exception:  # pragma: no cover - can't import GUI libs
    tk = None
    messagebox = None
    scrolledtext = None
    filedialog = None
    ttk = None

from hueyos.ai_tools_gui import run_ai_tools
from hueyos.config_toggle_gui import run_config_toggle_gui
from hueyos.dashboard import launch_dashboard
from hueyos.gui_scaling import apply_scaling
from hueyos.license_gui import show_license_gui
from hueyos.media_conversion import convert_media
from hueyos.scripts.preload_data import preload_all
from hueyos.services.container_management import (
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
from hueyos.simple_chat_gui import run_simple_chat

# Dark theme colors
# Updated to use a black background with green text and
# a dark purple accent for frames and windows.
DARK_BG = "#000000"  # black background
LIGHT_FG = "#00ff00"  # green foreground text
ACCENT_PURPLE = "#2d2b57"  # dark purple accent color


class MainUI:
    def __init__(self, root):
        if tk is None:
            raise RuntimeError("tkinter is not available")

        self.root = root
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
            except Exception:
                pass
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
        root = Path(__file__).resolve().parents[1]
        setup_dir = root / "setup"
        system = platform.system()
        if system == "Linux":
            self.install_path = setup_dir / "Debian13" / "install.sh"
            self.update_path = setup_dir / "Debian13" / "update.sh"
            self.run_path = root / "run.sh"
        elif system == "Darwin":
            self.install_path = setup_dir / "macOS" / "install.sh"
            self.update_path = setup_dir / "Debian13" / "update.sh"
            self.run_path = root / "run.sh"
        elif system == "Windows":
            self.install_path = setup_dir / "Windows11" / "01-FULL.bat"
            self.update_path = setup_dir / "Windows11" / "01-FULL.bat"
            self.run_path = root / "run.bat"
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
        self.log_text = scrolledtext.ScrolledText(
            self.root,
            width=100,
            height=25,
            bg=DARK_BG,
            fg=LIGHT_FG,
            insertbackground=LIGHT_FG,
            highlightbackground=ACCENT_PURPLE,
            highlightcolor=ACCENT_PURPLE,
            highlightthickness=2,
        )
        self.log_text.pack(pady=10)

        self.progress = ttk.Progressbar(
            self.root, orient=tk.HORIZONTAL, length=500, mode="determinate"
        )
        self.progress.pack(pady=10)

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
            self.root,
            text="Install",
            command=self.install,
            bg=ACCENT_PURPLE,
            fg=LIGHT_FG,
            activebackground=ACCENT_PURPLE,
            activeforeground=LIGHT_FG,
        )
        self.install_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.run_button = tk.Button(
            self.root,
            text="Run",
            command=self.run,
            bg=ACCENT_PURPLE,
            fg=LIGHT_FG,
            activebackground=ACCENT_PURPLE,
            activeforeground=LIGHT_FG,
        )
        self.run_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.update_button = tk.Button(
            self.root,
            text="Update",
            command=self.update,
            bg=ACCENT_PURPLE,
            fg=LIGHT_FG,
            activebackground=ACCENT_PURPLE,
            activeforeground=LIGHT_FG,
        )
        self.update_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.clear_button = tk.Button(
            self.root,
            text="Clear Log",
            command=self.clear_log,
            bg=ACCENT_PURPLE,
            fg=LIGHT_FG,
            activebackground=ACCENT_PURPLE,
            activeforeground=LIGHT_FG,
        )
        self.clear_button.pack(side=tk.LEFT, padx=10, pady=10)

    def log_message(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def clear_log(self) -> None:
        """Remove all text from the log window."""
        self.log_text.delete("1.0", tk.END)

    def run_script(self, script_path):
        if script_path is None or not Path(script_path).exists():
            messagebox.showerror(
                "Error", "Installer script not found for this platform."
            )
            return
        try:
            if str(script_path).endswith(".bat"):
                cmd = ["cmd", "/c", str(script_path)]
            else:
                cmd = ["bash", str(script_path)]
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            for line in iter(process.stdout.readline, b""):
                self.log_message(line.decode("utf-8").strip())
            process.stdout.close()
            process.wait()
            if process.returncode != 0:
                self.log_message(
                    f"Error: {process.stderr.read().decode('utf-8').strip()}"
                )
            else:
                self.log_message("Operation completed successfully.")
        except Exception as e:
            self.log_message(f"Exception: {str(e)}")
        finally:
            self.progress.stop()
            self.status_label.config(text="Status: Ready")

    def install(self):
        self.log_message("Starting installation...")
        self.status_label.config(text="Status: Installing")
        self.progress.start()
        self._submit_task(self.run_script, self.install_path)

    def run(self):
        self.log_message("Launching application...")
        self.status_label.config(text="Status: Running")
        self.progress.start()
        self._submit_task(self.run_script, self.run_path)

    def update(self):
        self.log_message("Starting update...")
        self.status_label.config(text="Status: Updating")
        self.progress.start()
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
        self._submit_task(run_config_toggle_gui)

    def _run_container_func(self, func, *args):
        try:
            func(*args)
            self.log_message("Operation completed successfully.")
        except Exception as exc:  # pragma: no cover - subprocess failures
            self.log_message(f"Exception: {exc}")
        finally:
            self.progress.stop()
            self.status_label.config(text="Status: Ready")

    def _submit_task(self, func, *args):
        executor = getattr(self, "executor", None)
        if executor is not None:
            executor.submit(func, *args)
        else:  # fallback for tests
            threading.Thread(target=func, args=args).start()

    def build_image(self):
        self.log_message("Building Docker image...")
        self.status_label.config(text="Status: Building")
        self.progress.start()
        self._submit_task(self._run_container_func, build_docker_image)

    def start_containers(self):
        self.log_message("Starting containers...")
        self.status_label.config(text="Status: Starting")
        self.progress.start()
        self._submit_task(self._run_container_func, manage_containers)

    def stop_containers(self):
        self.log_message("Stopping containers...")
        self.status_label.config(text="Status: Stopping")
        self.progress.start()
        self._submit_task(self._run_container_func, stop_containers)

    def cleanup_images(self):
        self.log_message("Pruning images...")
        self.status_label.config(text="Status: Cleaning")
        self.progress.start()
        self._submit_task(self._run_container_func, cleanup_images)

    def manage_volumes(self):
        self.log_message("Managing volumes...")
        self.status_label.config(text="Status: Volumes")
        self.progress.start()
        self._submit_task(self._run_container_func, manage_volumes)

    def manage_networks(self):
        self.log_message("Managing networks...")
        self.status_label.config(text="Status: Networks")
        self.progress.start()
        self._submit_task(self._run_container_func, manage_networks)

    def deploy_kubernetes(self):
        self.log_message("Deploying Kubernetes resources...")
        self.status_label.config(text="Status: Deploying")
        self.progress.start()
        self._submit_task(self._run_container_func, deploy_kubernetes)

    def cleanup_kubernetes(self):
        self.log_message("Cleaning Kubernetes resources...")
        self.status_label.config(text="Status: Cleaning")
        self.progress.start()
        self._submit_task(self._run_container_func, cleanup_kubernetes)

    def scale_deployment_prompt(self):
        name = simpledialog.askstring("Deployment", "Deployment name:")
        if not name:
            return
        replicas = simpledialog.askinteger("Replicas", "Number of replicas:")
        if replicas is None:
            return
        self.log_message(f"Scaling {name} to {replicas}...")
        self.status_label.config(text="Status: Scaling")
        self.progress.start()
        self._submit_task(self._run_container_func, scale_deployment, name, replicas)

    def get_pod_logs_prompt(self):
        pod = simpledialog.askstring("Pod", "Pod name:")
        if not pod:
            return
        self.log_message(f"Fetching logs for {pod}...")
        self.status_label.config(text="Status: Logs")
        self.progress.start()
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
        self.status_label.config(text="Status: Converting")
        self.progress.start()
        self._submit_task(self._convert_media_thread, src, dst, bitrate, codec)

    def _convert_media_thread(self, src, dst, bitrate, codec):
        try:
            convert_media(src, dst, bitrate=bitrate, codec=codec)
            self.log_message("Operation completed successfully.")
        except Exception as exc:  # pragma: no cover - ffmpeg errors
            self.log_message(f"Exception: {exc}")
        finally:
            self.progress.stop()
            self.status_label.config(text="Status: Ready")

    def _get_logs(self, pod):
        try:
            logs = get_pod_logs(pod)
            self.log_message(logs)
            self.log_message("Operation completed successfully.")
        except Exception as exc:  # pragma: no cover - subprocess failures
            self.log_message(f"Exception: {exc}")
        finally:
            self.progress.stop()
            self.status_label.config(text="Status: Ready")

    def launch_simple_chat(self):
        """Open the simple chat demo in a background thread."""
        self.log_message("Launching simple chat demo...")
        self._submit_task(run_simple_chat)

    def launch_ai_tools(self):
        """Open the AI tools window in a background thread."""
        self.log_message("Launching AI tools...")
        self._submit_task(run_ai_tools)

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
