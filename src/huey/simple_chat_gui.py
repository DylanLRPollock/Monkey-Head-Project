"""Simple Tkinter chat demonstration."""

from __future__ import annotations

import tkinter as tk
from tkinter import scrolledtext

from huey.gui_scaling import apply_scaling

DARK_BG = "#101418"
PANEL_BG = "#172027"
TEXT_FG = "#eef5f1"
ACCENT = "#2f7d6d"

KNOWN_ANSWERS = {
    "what is the capital of france?": "The capital of France is Paris.",
}


def get_answer(question: str) -> str:
    normalized = question.strip().lower()
    return KNOWN_ANSWERS.get(normalized, "Sorry, I don't know the answer to that.")


def run_simple_chat() -> None:  # pragma: no cover - exercised via monkeypatch
    root = tk.Tk()
    root.title("Simple Chat")
    if hasattr(root, "minsize"):
        root.minsize(520, 420)
    if hasattr(root, "configure"):
        root.configure(bg=DARK_BG)
    apply_scaling(root, mode="1080p")

    chat = scrolledtext.ScrolledText(
        root,
        state=tk.DISABLED,
        wrap=tk.WORD,
        bg=PANEL_BG,
        fg=TEXT_FG,
        insertbackground=TEXT_FG,
        height=16,
    )

    input_frame = tk.Frame(root, bg=DARK_BG) if hasattr(tk, "Frame") else root
    entry = tk.Entry(
        input_frame,
        bg=PANEL_BG,
        fg=TEXT_FG,
        insertbackground=TEXT_FG,
    )

    def send_message():
        question = entry.get().strip()
        if not question:
            return
        answer = get_answer(question)
        chat.config(state=tk.NORMAL)
        chat.insert(tk.END, f"You: {question}\n")
        chat.insert(tk.END, f"Bot: {answer}\n")
        chat.config(state=tk.DISABLED)
        if hasattr(chat, "see"):
            chat.see(tk.END)
        entry.delete(0, tk.END)

    if hasattr(entry, "bind"):
        entry.bind("<Return>", lambda _event: send_message())
    send_button = tk.Button(
        input_frame,
        text="Send",
        command=send_message,
        bg=ACCENT,
        fg=TEXT_FG,
        activebackground=ACCENT,
        activeforeground=TEXT_FG,
    )
    chat.pack(fill="both", expand=True, padx=12, pady=(12, 8))
    if input_frame is not root:
        input_frame.pack(fill="x", padx=12, pady=(0, 12))
    entry.pack(side="left", fill="x", expand=True)
    send_button.pack(side="left", padx=(8, 0))

    root.mainloop()


__all__ = ["get_answer", "run_simple_chat"]
