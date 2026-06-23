"""Simple Tkinter chat demonstration aligned with the HueyOS launcher."""

from __future__ import annotations

import tkinter as tk
from tkinter import scrolledtext

from huey.gui.theme import as_tk_palette
from huey.gui_scaling import apply_scaling

_PALETTE = as_tk_palette()
DARK_BG = _PALETTE["background"]
PANEL_BG = _PALETTE["panel"]
PANEL_ALT_BG = _PALETTE["panel_alt"]
TEXT_FG = _PALETTE["text"]
MUTED_FG = _PALETTE["muted_text"]
ACCENT = _PALETTE["accent"]

KNOWN_ANSWERS = {
    "what is the capital of france?": "The capital of France is Paris.",
    "what is 2+2?": "2 + 2 equals 4.",
}


def get_answer(question: str) -> str:
    normalized = question.strip().lower()
    return KNOWN_ANSWERS.get(normalized, "Sorry, I don't know the answer to that.")


def run_simple_chat() -> None:  # pragma: no cover - exercised via monkeypatch
    end_token = getattr(tk, "END", "end")
    normal_state = getattr(tk, "NORMAL", "normal")
    disabled_state = getattr(tk, "DISABLED", "disabled")
    word_wrap = getattr(tk, "WORD", "word")
    root = tk.Tk()
    root.title("HueyOS Chat Console")
    if hasattr(root, "minsize"):
        root.minsize(520, 420)
    if hasattr(root, "configure"):
        root.configure(bg=DARK_BG)
    apply_scaling(root, mode="1080p")

    container = tk.Frame(root, bg=DARK_BG) if hasattr(tk, "Frame") else root
    if container is not root and hasattr(container, "pack"):
        container.pack(fill="both", expand=True, padx=12, pady=12)

    if hasattr(tk, "Label"):
        header_parent = (
            tk.Frame(container, bg=PANEL_BG) if hasattr(tk, "Frame") else container
        )
        if header_parent is not container and hasattr(header_parent, "pack"):
            header_parent.pack(fill="x", pady=(0, 10))
        tk.Label(
            header_parent,
            text="HueyOS Chat Console",
            bg=PANEL_BG,
            fg=TEXT_FG,
        ).pack(anchor="w", padx=12, pady=(12, 4))
        tk.Label(
            header_parent,
            text=(
                "Keep the launcher open while this window handles quick prompts and "
                "canned answers."
            ),
            bg=PANEL_BG,
            fg=MUTED_FG,
            justify="left",
            wraplength=480,
        ).pack(anchor="w", padx=12, pady=(0, 12))

    chat = scrolledtext.ScrolledText(
        container,
        state=disabled_state,
        wrap=word_wrap,
        bg=PANEL_BG,
        fg=TEXT_FG,
        insertbackground=TEXT_FG,
        height=16,
    )

    input_frame = tk.Frame(container, bg=DARK_BG) if hasattr(tk, "Frame") else container
    entry = tk.Entry(
        input_frame,
        bg=PANEL_ALT_BG,
        fg=TEXT_FG,
        insertbackground=TEXT_FG,
    )

    def send_message():
        question = entry.get().strip()
        if not question:
            return
        answer = get_answer(question)
        chat.config(state=normal_state)
        chat.insert(end_token, f"You: {question}\n")
        chat.insert(end_token, f"HueyOS: {answer}\n\n")
        chat.config(state=disabled_state)
        if hasattr(chat, "see"):
            chat.see(end_token)
        entry.delete(0, end_token)

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
    chat.pack(fill="both", expand=True, padx=12, pady=(0, 8))
    if input_frame is not container:
        input_frame.pack(fill="x", pady=(0, 12))
    entry.pack(side="left", fill="x", expand=True)
    send_button.pack(side="left", padx=(8, 0))

    chat.config(state=normal_state)
    chat.insert(
        end_token,
        "HueyOS: Ready. Try 'What is the capital of France?' or 'What is 2+2?'\n\n",
    )
    chat.config(state=disabled_state)

    root.mainloop()


__all__ = ["get_answer", "run_simple_chat"]


if __name__ == "__main__":
    run_simple_chat()
