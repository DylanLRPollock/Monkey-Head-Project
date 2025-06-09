# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
import platform
import subprocess
import threading
from pathlib import Path

try:  # pragma: no cover - optional dependency
    import tkinter as tk
    from tkinter import messagebox, scrolledtext, ttk
except Exception:  # pragma: no cover - can't import GUI libs
    tk = None
    messagebox = None
    scrolledtext = None
    ttk = None

from monkey_head.license_gui import show_license_gui
from monkey_head.scripts.preload_data import preload_all


class MainUI:
    def __init__(self, root):
        if tk is None:
            raise RuntimeError("tkinter is not available")

        self.root = root
        self.root.title("Program Manager")
        self.setup_paths()
        self.create_menu()
        self.create_widgets()
        self.check_license()

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
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Install", command=self.install)
        file_menu.add_command(label="Run", command=self.run)
        file_menu.add_command(label="Update", command=self.update)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

        tools_menu = tk.Menu(menu_bar, tearoff=0)
        tools_menu.add_command(label="License", command=self.show_license)
        tools_menu.add_command(label="Data Summary", command=self.show_data_summary)
        menu_bar.add_cascade(label="Tools", menu=tools_menu)

    def create_widgets(self):
        self.log_text = scrolledtext.ScrolledText(self.root, width=80, height=20)
        self.log_text.pack(pady=10)

        self.progress = ttk.Progressbar(
            self.root, orient=tk.HORIZONTAL, length=400, mode="determinate"
        )
        self.progress.pack(pady=10)

        self.status_label = tk.Label(
            self.root, text="Status: Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM, ipady=2)

        self.install_button = tk.Button(self.root, text="Install", command=self.install)
        self.install_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.run_button = tk.Button(self.root, text="Run", command=self.run)
        self.run_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.update_button = tk.Button(self.root, text="Update", command=self.update)
        self.update_button.pack(side=tk.LEFT, padx=10, pady=10)

    def log_message(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

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
        threading.Thread(target=self.run_script, args=(self.install_path,)).start()

    def run(self):
        self.log_message("Launching application...")
        self.status_label.config(text="Status: Running")
        self.progress.start()
        threading.Thread(target=self.run_script, args=(self.run_path,)).start()

    def update(self):
        self.log_message("Starting update...")
        self.status_label.config(text="Status: Updating")
        self.progress.start()
        threading.Thread(target=self.run_script, args=(self.update_path,)).start()

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
            "Data Summary",
            f"Prompts: {prompts}\nMemory files: {memory_files}"
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = MainUI(root)
    root.mainloop()
