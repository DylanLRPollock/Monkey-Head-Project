"""Simple Tkinter chat demonstration."""

from __future__ import annotations

import tkinter as tk
from tkinter import scrolledtext

from hueyos.gui_scaling import apply_scaling


KNOWN_ANSWERS = {
    "what is the capital of france?": "The capital of France is Paris.",
}


def get_answer(question: str) -> str:
    normalized = question.strip().lower()
    return KNOWN_ANSWERS.get(normalized, "Sorry, I don't know the answer to that.")


def run_simple_chat() -> None:  # pragma: no cover - exercised via monkeypatch
    root = tk.Tk()
    root.title("Simple Chat")
    apply_scaling(root, mode="custom" if tk is None else "1080p")

    chat = scrolledtext.ScrolledText(root, state=tk.NORMAL)
    entry = tk.Entry(root)

    def send_message():
        question = entry.get()
        answer = get_answer(question)
        chat.insert(tk.END, f"You: {question}\n")
        chat.insert(tk.END, f"Bot: {answer}\n")
        entry.delete(0, tk.END)

    send_button = tk.Button(root, text="Send", command=send_message)
    for widget in (chat, entry, send_button):
        widget.pack()

    root.mainloop()


__all__ = ["get_answer", "run_simple_chat"]
