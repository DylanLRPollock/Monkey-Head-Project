# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
try:  # pragma: no cover - optional dependency
    import tkinter as tk
    from tkinter import messagebox
    from .gui_scaling import apply_scaling
except Exception:  # pragma: no cover - can't import GUI libs
    tk = None
    messagebox = None


def create_tkinter_window(mode: str = "4k"):
    """
    Creates a simple Tkinter window with a button that shows a message box.
    """
    if tk is None:
        raise RuntimeError("tkinter is not available")

    root = tk.Tk()
    apply_scaling(root, mode)
    root.title("Tkinter Window")

    def show_message():
        messagebox.showinfo("Message", "Hello, Tkinter!")

    button = tk.Button(root, text="Click Me", command=show_message)
    button.pack(pady=20)

    root.mainloop()


if __name__ == "__main__":
    create_tkinter_window()
