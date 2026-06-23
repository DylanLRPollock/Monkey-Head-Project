#!/usr/bin/env python3
# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: List Registered Functions module (huey/memory/PY)

"""Print functions registered in ``huey.os.function_registry``."""

from huey.os.function_registry import ensure_registered_functions, list_functions


def main() -> None:
    ensure_registered_functions()
    for name in list_functions():
        print(name)


if __name__ == "__main__":  # pragma: no cover - CLI utility
    main()
