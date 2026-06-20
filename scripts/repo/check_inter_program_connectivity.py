"""Connectivity self-check stub."""

from __future__ import annotations


def check_inter_program_connectivity() -> bool:
    return True


def main() -> int:
    return 0 if check_inter_program_connectivity() else 1


__all__ = ["check_inter_program_connectivity", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
