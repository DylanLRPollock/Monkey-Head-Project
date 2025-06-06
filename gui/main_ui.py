# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import subprocess
import threading

class MainUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Program Manager")
        self.create_menu()
        self.create_widgets()

    def create_menu(self):
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Install", command=self.install)
        file_menu.add_command(label="Update", command=self.update)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

    def create_widgets(self):
        self.log_text = scrolledtext.ScrolledText(self.root, width=80, height=20)
        self.log_text.pack(pady=10)

        self.progress = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress.pack(pady=10)

        self.status_label = tk.Label(self.root, text="Status: Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM, ipady=2)

        self.install_button = tk.Button(self.root, text="Install", command=self.install)
        self.install_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.update_button = tk.Button(self.root, text="Update", command=self.update)
        self.update_button.pack(side=tk.RIGHT, padx=10, pady=10)

    def log_message(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def run_script(self, script_path):
        try:
            process = subprocess.Popen(["bash", script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            for line in iter(process.stdout.readline, b''):
                self.log_message(line.decode('utf-8').strip())
            process.stdout.close()
            process.wait()
            if process.returncode != 0:
                self.log_message(f"Error: {process.stderr.read().decode('utf-8').strip()}")
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
        threading.Thread(target=self.run_script, args=("H:\\setup\\install.sh",)).start()

    def update(self):
        self.log_message("Starting update...")
        self.status_label.config(text="Status: Updating")
        self.progress.start()
        threading.Thread(target=self.run_script, args=("H:\\setup\\update.sh",)).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = MainUI(root)
    root.mainloop()
