# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
import tkinter as tk
from tkinter import messagebox


def create_tkinter_window():
    """
    Creates a simple Tkinter window with a button that shows a message box.
    """
    root = tk.Tk()
    root.title("Tkinter Window")

    def show_message():
        messagebox.showinfo("Message", "Hello, Tkinter!")

    button = tk.Button(root, text="Click Me", command=show_message)
    button.pack(pady=20)

    root.mainloop()


if __name__ == "__main__":
    create_tkinter_window()
