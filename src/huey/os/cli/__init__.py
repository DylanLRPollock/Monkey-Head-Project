"""Maintained CLI namespace scaffold for :mod:`hueyos`."""

from __future__ import annotations

from collections.abc import Iterable
from importlib import import_module

from huey.os.core.platform_support import split_command_line
from huey.os.config_manager import ConfigManager

from .main import build_parser


class CLI:
    """Small interactive settings shell retained for legacy callers."""

    def __init__(self, config_path: str | None = None) -> None:
        self.config_manager = ConfigManager(config_path)

    def _execute(self, command_line: str) -> bool:
        parts = split_command_line(command_line)
        if not parts:
            return True

        command, *args = parts
        if command in {"exit", "quit"}:
            return False
        if command == "set" and len(args) >= 2:
            key = args[0]
            value = " ".join(args[1:])
            self.config_manager.set_setting(key, value)
            return True
        if command == "get" and len(args) == 1:
            value = self.config_manager.get_setting(args[0])
            if value is not None:
                print(value)
            return True
        raise ValueError(f"Unknown command: {command}")

    def run(self) -> None:
        while True:
            try:
                command_line = input("> ")
            except EOFError:  # pragma: no cover - interactive convenience
                break
            if not command_line.strip():
                continue
            if not self._execute(command_line):
                break


def main(argv: Iterable[str] | None = None) -> int:
    legacy_cli = import_module("huey.memory.PY.cli")
    return legacy_cli.main(list(argv) if argv is not None else None)


__all__ = ["CLI", "build_parser", "main"]
