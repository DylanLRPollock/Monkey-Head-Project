# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Pygpt Custom Cli module (huey)

"""Lightweight CLI integration mimicking the legacy PyGPT launcher."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .pygpt_memory import Memory


class CustomPyGPT:
    """A minimal chatbot used when full PyGPT dependencies are unavailable."""

    def __init__(self, prompt_file: str | Path | None = None):
        if prompt_file is None:
            prompt_file = (
                Path(__file__).resolve().parent.parent
                / "huey"
                / "memory"
                / "PY"
                / "prompts"
                / "huey_main_prompt.txt"
            )
        self.prompt_file = Path(prompt_file)
        self.memory = Memory()
        self.main_prompt = self.load_main_prompt()

    def load_main_prompt(self) -> str:
        """Load the default main prompt from ``self.prompt_file`` if it exists."""

        try:
            return self.prompt_file.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            return ""

    def generate_reply(self, message: str) -> str:
        """Generate a trivial echo-style reply."""

        return f"Echo: {message}"

    def _handle_list_pdfs(self) -> Iterable[str]:
        """Return available PDF names by deferring to :mod:`monkey_head.pdf_utils`."""

        from .pdf_utils import list_available_pdfs

        yield from list_available_pdfs()

    def run_cli(self) -> None:
        """Run an interactive CLI loop suitable for simple testing."""

        print("Custom PyGPT CLI. Type 'exit' to quit.")
        user_prompt = input(
            "Enter main prompt or press Enter to use default:\n"
            f"{self.main_prompt}\n> "
        ).strip()
        if user_prompt:
            self.main_prompt = user_prompt
        print("Chat starting...")
        while True:
            try:
                user_input = input("You: ")
            except EOFError:  # pragma: no cover - interactive convenience
                break
            command = user_input.strip().lower()
            if command == "list pdfs":
                print("Available PDFs:")
                for name in self._handle_list_pdfs():
                    print(f"- {name}")
                continue
            if command in {"exit", "quit"}:
                break
            self.memory.add_user_message(user_input)
            reply = self.generate_reply(user_input)
            self.memory.add_assistant_message(reply)
            print(f"Bot: {reply}")


__all__ = ["CustomPyGPT"]
