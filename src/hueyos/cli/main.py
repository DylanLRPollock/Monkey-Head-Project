"""Shared CLI builders for the maintained :mod:`hueyos` namespace."""

from __future__ import annotations

import argparse
from typing import Callable

from .commands import register_memory_commands, register_runtime_commands, register_system_commands


ParserHandler = Callable[[argparse.Namespace], int]


def build_parser(*, prog: str = "huey") -> argparse.ArgumentParser:
    """Build the Huey CLI parser while delegating command wiring by domain."""

    parser = argparse.ArgumentParser(
        prog=prog,
        description="Command line interface for HueyOS runtime and utilities.",
    )
    sub = parser.add_subparsers(dest="command")
    sub.required = True

    register_runtime_commands(sub)
    register_system_commands(sub)
    register_memory_commands(sub)

    return parser
