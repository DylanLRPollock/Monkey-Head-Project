"""Command registration helpers for the maintained HueyOS CLI."""

from .memory import register_memory_commands
from .runtime import register_runtime_commands
from .system import register_system_commands

__all__ = [
    "register_memory_commands",
    "register_runtime_commands",
    "register_system_commands",
]
