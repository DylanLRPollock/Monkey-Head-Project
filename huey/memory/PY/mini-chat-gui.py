# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Mini Chat Gui module (huey/memory/PY)

import tkinter as tk
from tkinter import scrolledtext

# Simple question-answer logic


def get_answer(question: str) -> str:
    q = question.lower().strip()
    if "capital of france" in q:
        return "The capital of France is Paris."
    if "2+2" in q or "two plus two" in q:
        return "2 + 2 equals 4."
    return "Sorry, I do not know the answer."


def on_ask() -> None:
    question = entry.get()
    if not question:
        return
    answer = get_answer(question)
    chat_box.config(state=tk.NORMAL)
    chat_box.insert(tk.END, f"Q: {question}\n")
    chat_box.insert(tk.END, f"A: {answer}\n\n")
    chat_box.config(state=tk.DISABLED)
    entry.delete(0, tk.END)


root = tk.Tk()
root.title("Mini Chat")

entry = tk.Entry(root, width=60)
entry.pack(padx=10, pady=5)

button = tk.Button(root, text="Ask", command=on_ask)
button.pack(pady=5)

chat_box = scrolledtext.ScrolledText(root, width=70, height=15, state=tk.DISABLED)
chat_box.pack(padx=10, pady=5)

root.mainloop()
