"""Custom PyGPT command-line interface stub."""

from __future__ import annotations

from pathlib import Path


class CustomPyGPT:
    def __init__(self, prompt_file: str | Path | None = None):
        self.prompt_file = Path(prompt_file) if prompt_file else None
        if self.prompt_file and self.prompt_file.exists():
            self.main_prompt = self.prompt_file.read_text()
        else:
            self.main_prompt = "Echo mode"

    def generate_reply(self, message: str) -> str:
        return f"Echo: {message}"


__all__ = ["CustomPyGPT"]
