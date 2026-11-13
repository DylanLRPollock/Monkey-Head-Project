"""Tkinter port of the supplied dual-agreement application.

The supplied source includes the complete MIT notice and only an excerpt of
GPL-3.0's preamble. This UI labels that excerpt clearly and links to the full
license so it cannot be mistaken for the complete license text.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Final

BACKGROUND: Final = "#171323"
CARD: Final = "#282238"
CARD_ALT: Final = "#211c30"
PURPLE: Final = "#7657a8"
GREEN: Final = "#4bc28b"
TEXT: Final = "#f4f1f8"
MUTED: Final = "#c5bdcf"

MIT_TEXT: Final = """MIT License

Copyright (c) 2026 Marcin Szczygliński
GitHub: https://github.com/szczyglis-dev/py-gpt

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

GPL_EXCERPT: Final = """GNU General Public License, version 3 — excerpt

Full license: https://www.gnu.org/licenses/gpl-3.0.html

Preamble

The GNU General Public License is a free, copyleft license for software and
other kinds of works.

The licenses for most software and other practical works are designed to take
away your freedom to share and change the works. By contrast, the GNU General
Public License is intended to guarantee your freedom to share and change all
versions of a program—to make sure it remains free software for all its users.
We, the Free Software Foundation, use the GNU General Public License for most
of our software; it applies also to any other work released this way by its
authors. You can apply it to your programs, too.

When we speak of free software, we are referring to freedom, not price. Our
General Public Licenses are designed to make sure that you have the freedom to
distribute copies of free software (and charge for them if you wish), that you
receive source code or can get it if you want it, that you can change the
software or use pieces of it in new free programs, and that you know you can
do these things.

To protect your rights, we need to prevent others from denying you these rights
or asking you to surrender the rights. Therefore, you have certain
responsibilities if you distribute copies of the software, or if you modify
it: responsibilities to respect the freedom of others.

This is an excerpt from the supplied application, not the complete GPL-3.0
license. Review the full license at the link above before accepting."""

AGREEMENTS: Final = (
    {
        "title": "Original Agreement",
        "description": (
            "Please review and accept the following terms and conditions "
            "to continue."
        ),
        "acceptance": (
            "I have read and agree to the terms and conditions outlined "
            "in the Original Agreement."
        ),
        "document": MIT_TEXT,
        "button": "Continue",
    },
    {
        "title": "Our Agreement",
        "description": (
            "One more agreement to review before we finalize everything."
        ),
        "acceptance": (
            "I have read and agree to the additional terms outlined "
            "in Our Agreement."
        ),
        "document": GPL_EXCERPT,
        "button": "Complete",
    },
)


class AgreementApp(tk.Tk):
    """A linear agreement review flow; acceptances are not persisted."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Agreement Review")
        self.configure(background=BACKGROUND)
        self.minsize(560, 620)
        self.geometry("760x760")
        self.resizable(True, True)

        self._step = 0
        self._accepted = tk.BooleanVar(value=False)
        self._countdown = 5
        self._timer_id: str | None = None

        self._configure_styles()
        self._center_window()
        self._build_shell()
        self._show_agreement()

        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Agreement.Horizontal.TProgressbar",
            troughcolor="#3b334a",
            background=GREEN,
            bordercolor="#3b334a",
            lightcolor=GREEN,
            darkcolor=GREEN,
        )
        style.configure(
            "Agreement.TCheckbutton",
            background=CARD_ALT,
            foreground=TEXT,
            font=("TkDefaultFont", 10),
            padding=8,
        )
        style.map(
            "Agreement.TCheckbutton",
            background=[("active", CARD_ALT)],
            foreground=[("disabled", MUTED)],
        )
        style.configure(
            "Agreement.TButton",
            font=("TkDefaultFont", 11, "bold"),
            padding=(14, 10),
        )
        style.map(
            "Agreement.TButton",
            background=[("!disabled", GREEN), ("disabled", "#514b5b")],
            foreground=[("!disabled", "#10251b"), ("disabled", "#b5afbc")],
        )

    def _center_window(self) -> None:
        self.update_idletasks()
        width, height = 760, 760
        left = max(0, (self.winfo_screenwidth() - width) // 2)
        top = max(0, (self.winfo_screenheight() - height) // 2)
        self.geometry(f"{width}x{height}+{left}+{top}")

    def _build_shell(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.progress = ttk.Progressbar(
            self,
            style="Agreement.Horizontal.TProgressbar",
            maximum=100,
            value=33,
        )
        self.progress.grid(row=0, column=0, sticky="ew", padx=30, pady=(28, 16))

        self.card = tk.Frame(
            self,
            background=CARD,
            highlightbackground="#66527f",
            highlightthickness=1,
            padx=26,
            pady=24,
        )
        self.card.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 30))
        self.card.columnconfigure(0, weight=1)

        self.header = tk.Frame(self.card, background=CARD)
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.columnconfigure(0, weight=1)

        self.step_label = tk.Label(
            self.header,
            background="#3c3151",
            foreground=GREEN,
            font=("TkDefaultFont", 9, "bold"),
            padx=12,
            pady=6,
        )
        self.step_label.grid(row=0, column=0, sticky="w")

        self.title_label = tk.Label(
            self.card,
            background=CARD,
            foreground=TEXT,
            font=("Georgia", 24, "bold"),
            anchor="w",
        )
        self.title_label.grid(row=1, column=0, sticky="ew", pady=(18, 4))

        self.description_label = tk.Label(
            self.card,
            background=CARD,
            foreground=MUTED,
            font=("TkDefaultFont", 10),
            anchor="w",
            justify="left",
            wraplength=640,
        )
        self.description_label.grid(row=2, column=0, sticky="new", pady=(0, 16))

        document_frame = tk.Frame(
            self.card,
            background=CARD_ALT,
            highlightbackground="#59466f",
            highlightthickness=1,
        )
        document_frame.grid(row=3, column=0, sticky="nsew")
        document_frame.columnconfigure(0, weight=1)
        document_frame.rowconfigure(0, weight=1)
        self.card.rowconfigure(3, weight=1)

        self.document = tk.Text(
            document_frame,
            wrap="word",
            background=CARD_ALT,
            foreground=TEXT,
            insertbackground=TEXT,
            selectbackground=PURPLE,
            relief="flat",
            borderwidth=0,
            padx=18,
            pady=16,
            font=("Georgia", 11),
            spacing1=2,
            spacing3=8,
            state="disabled",
            cursor="arrow",
        )
        scrollbar = ttk.Scrollbar(
            document_frame,
            orient="vertical",
            command=self.document.yview,
        )
        self.document.configure(yscrollcommand=scrollbar.set)
        self.document.grid(row=0, column=0, sticky="nsew", padx=(1, 0), pady=1)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=1, padx=(0, 1))

        self.accept_check = ttk.Checkbutton(
            self.card,
            style="Agreement.TCheckbutton",
            variable=self._accepted,
            command=self._update_continue_state,
        )
        self.accept_check.grid(row=4, column=0, sticky="ew", pady=(16, 12))

        self.continue_button = ttk.Button(
            self.card,
            style="Agreement.TButton",
            command=self._continue,
            state="disabled",
        )
        self.continue_button.grid(row=5, column=0, sticky="ew")

    def _show_agreement(self) -> None:
        agreement = AGREEMENTS[self._step]
        self.progress.configure(value=33 if self._step == 0 else 66)
        self.step_label.configure(text=f"STEP {self._step + 1} OF 3")
        self.title_label.configure(text=agreement["title"])
        self.description_label.configure(text=agreement["description"])
        self._accepted.set(False)
        self.accept_check.configure(text=agreement["acceptance"])
        self.continue_button.configure(text=agreement["button"], state="disabled")

        self.document.configure(state="normal")
        self.document.delete("1.0", "end")
        self.document.insert("1.0", agreement["document"])
        self.document.configure(state="disabled")
        self.document.yview_moveto(0)

    def _update_continue_state(self) -> None:
        state = "normal" if self._accepted.get() else "disabled"
        self.continue_button.configure(state=state)

    def _continue(self) -> None:
        if not self._accepted.get():
            return
        if self._step == 0:
            self._step = 1
            self._show_agreement()
            return
        self._show_completion()

    def _show_completion(self) -> None:
        self.progress.configure(value=100)
        for child in self.card.winfo_children():
            child.destroy()

        self.card.rowconfigure(0, weight=1)
        completion = tk.Frame(self.card, background=CARD)
        completion.grid(row=0, column=0, sticky="nsew")
        completion.columnconfigure(0, weight=1)
        completion.rowconfigure(0, weight=1)

        content = tk.Frame(completion, background=CARD)
        content.grid(row=0, column=0)
        tk.Label(
            content,
            text="✓",
            background="#2d493d",
            foreground=GREEN,
            font=("TkDefaultFont", 42, "bold"),
            width=3,
            height=1,
        ).pack(pady=(0, 18))
        tk.Label(
            content,
            text="Thank You!",
            background=CARD,
            foreground=TEXT,
            font=("Georgia", 30, "bold"),
        ).pack(pady=(0, 8))
        tk.Label(
            content,
            text=(
                "You have completed both agreement review steps.\n"
                "This window will close automatically."
            ),
            background=CARD,
            foreground=MUTED,
            font=("TkDefaultFont", 11),
            justify="center",
        ).pack(pady=(0, 20))

        self.countdown_label = tk.Label(
            content,
            text="Closing in 5 seconds",
            background="#332a42",
            foreground=GREEN,
            font=("TkDefaultFont", 11, "bold"),
            padx=16,
            pady=10,
        )
        self.countdown_label.pack()
        tk.Label(
            content,
            text="This demo does not save or transmit acceptance records.",
            background=CARD,
            foreground=MUTED,
            font=("TkDefaultFont", 9),
        ).pack(pady=(20, 0))

        self.progress.configure(value=100)
        self._timer_id = self.after(1000, self._tick)

    def _tick(self) -> None:
        self._countdown -= 1
        if self._countdown <= 0:
            self.destroy()
            return
        self.countdown_label.configure(
            text=f"Closing in {self._countdown} second"
            f"{'' if self._countdown == 1 else 's'}"
        )
        self._timer_id = self.after(1000, self._tick)


def main() -> None:
    """Launch the desktop agreement review flow."""
    AgreementApp().mainloop()


if __name__ == "__main__":
    main()
