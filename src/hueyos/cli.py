"""Lightweight command-line interface used in tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class _SimpleConfig:
    """Minimal configuration store backing :class:`CLI`.

    The real project uses a richer configuration system. For the purposes of
    the unit tests we just need to persist key/value pairs in memory.
    """

    data: Dict[str, str] = field(default_factory=dict)

    def set_setting(self, key: str, value: str) -> None:
        self.data[key] = value

    def get_setting(self, key: str, default=None):
        return self.data.get(key, default)


class CLI:
    """Tiny REPL that understands ``set``/``get`` commands."""

    def __init__(self):
        self.config_manager = _SimpleConfig()

    def run(self) -> None:
        while True:
            command = input("Enter command (type 'exit' to quit): ")
            if command == "exit":
                break
            if command.startswith("set "):
                try:
                    _, key, value = command.split(maxsplit=2)
                except ValueError:
                    print("Usage: set <key> <value>")
                    continue
                self.config_manager.set_setting(key, value)
            elif command.startswith("get "):
                _, key = command.split(maxsplit=1)
                value = self.config_manager.get_setting(key, "")
                print(value)
            else:
                print("Unknown command")


__all__ = ["CLI"]
