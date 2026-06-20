"""CLI helpers for the UI control surface."""

from __future__ import annotations

import argparse


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Huey UI control surface")
    parser.add_argument("--mode", default="summary", choices=["summary", "diagnostics", "control"])
    parser.add_argument("--format", default="table", choices=["table", "json"])
    return parser


__all__ = ["build_cli_parser"]
