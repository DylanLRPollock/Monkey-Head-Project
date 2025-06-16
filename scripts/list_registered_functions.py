#!/usr/bin/env python3
"""Print functions registered in ``monkey_head.function_registry``."""

from monkey_head.function_registry import list_functions


def main() -> None:
    for name in list_functions():
        print(name)


if __name__ == "__main__":  # pragma: no cover - CLI utility
    main()
