"""Minimal GUI scaffolding for tests."""

from __future__ import annotations

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog


def show_license_gui():
    messagebox.showinfo("License", "License details")


def preload_all():
    return {}


def convert_media(input_path: str, output_path: str, **kwargs):
    return None


def run_simple_chat():
    return None


def run_ai_tools():
    return None


class MainUI:
    def check_license(self):
        show_license_gui()

    def show_license(self):
        show_license_gui()

    def show_data_summary(self):
        data = preload_all()
        messagebox.showinfo("Data Summary", str(data))

    def choose_screen_mode(self):
        mode = os.environ.get("SCREEN_MODE")
        if mode:
            return mode
        choice = simpledialog.askstring("Screen Mode", "Enter screen mode")
        if choice == "custom":
            simpledialog.askfloat("Scaling", "Enter scale factor")
            simpledialog.askinteger("Font Size", "Enter font size")
        return choice

    def _run_container_func(self, *args):
        return None

    def build_image(self):
        threading.Thread(target=self._run_container_func, args=()).start()

    def deploy_kubernetes(self):
        threading.Thread(target=self._run_container_func, args=()).start()

    def scale_deployment_prompt(self):
        deployment = simpledialog.askstring("Deployment", "Enter deployment name")
        replicas = simpledialog.askinteger("Replicas", "How many replicas?")
        threading.Thread(target=self._run_container_func, args=(deployment, replicas)).start()

    def convert_media_prompt(self):
        input_path = filedialog.askopenfilename()
        output_path = filedialog.asksaveasfilename()
        bitrate = simpledialog.askstring("Bitrate", "Enter bitrate")
        codec = simpledialog.askstring("Codec", "Enter codec")
        threading.Thread(
            target=convert_media,
            args=(input_path, output_path),
            kwargs={"bitrate": bitrate, "codec": codec},
        ).start()

    def launch_simple_chat(self):
        threading.Thread(target=run_simple_chat, args=()).start()

    def launch_ai_tools(self):
        threading.Thread(target=run_ai_tools, args=()).start()

    def log_message(self, *args, **kwargs):
        pass

    def clear_log(self):
        self.log_text.delete("1.0", tk.END)


__all__ = ["MainUI", "show_license_gui", "run_simple_chat", "run_ai_tools", "convert_media", "preload_all"]
