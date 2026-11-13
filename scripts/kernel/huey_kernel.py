#!/usr/bin/env python3
"""Entry-point launcher for the HueyOS kernel builder CLI.

This is a thin wrapper: no business logic, no argument parsing, no
subcommand dispatch. It does three things and nothing more:

1. Ensures the checkout's ``src/`` directory is on ``sys.path`` so the
   framework is importable from an uninstalled checkout.
2. Sets ``sys.argv`` to ``["huey-kernel", *argv]`` so the delegated CLI's
   ``argparse`` reads the caller's arguments (and ``sys.argv[0]`` is a
   stable program name, not the script's full path).
3. Calls ``huey.kernel_build.cli.main()`` and exits with its return code
   (0 if it returns ``None``, which is the standard argparse pattern).

Import safety
-------------
Loading this file as a module (``importlib``, ``pytest``) performs no I/O
and no CLI invocation: the ``if __name__ == "__main__"`` guard prevents the
entry block from running, and the ``huey.kernel_build.cli`` import is
inside ``_main()`` so module load does not require the CLI to exist yet.

Pre-Step-21 behavior
--------------------
While ``huey.kernel_build.cli`` is not yet implemented, ``_main`` catches
``ImportError``, prints a diagnostic to stderr, and returns 3 (missing
prerequisites per the framework's exit-code convention). The launcher
becomes fully functional automatically once Step 21 lands the CLI.
"""

from __future__ import annotations

import sys
from pathlib import Path

__all__ = ["_main", "_repo_src_dir"]

#: Program name used for ``sys.argv[0]`` so argparse error messages are
#: stable and independent of the script's install path.
_PROGRAM_NAME = "huey-kernel"

#: Exit code returned when the CLI module is missing (missing prerequisites).
_EXIT_CLI_MISSING = 3


def _repo_src_dir() -> Path:
    """Return ``<repo>/src`` derived from this script's location."""
    return Path(__file__).resolve().parent.parent.parent / "src"


def _main(argv: list[str]) -> int:
    """Delegate to the CLI, returning its exit code.

    Parameters
    ----------
    argv:
        Arguments passed to the launcher (i.e. ``sys.argv[1:]`` at call
        time). They are forwarded as ``sys.argv[1:]`` to the CLI.

    Returns
    -------
    int
        The CLI's return code, or 0 if it returned ``None``, or
        ``_EXIT_CLI_MISSING`` (3) if ``huey.kernel_build.cli`` is not
        importable.
    """
    src = _repo_src_dir()
    if src.is_dir():
        src_str = str(src)
        if src_str not in sys.path:
            sys.path.insert(0, src_str)

    try:
        from huey.kernel_build.cli import main as _cli_main
    except ImportError as exc:
        print(
            f"{_PROGRAM_NAME}: CLI not yet available "
            f"(huey.kernel_build.cli: {exc}). "
            "Step 21 of the handoff introduces the CLI subcommands; "
            "this launcher will delegate to it once present.",
            file=sys.stderr,
        )
        return _EXIT_CLI_MISSING

    saved_argv = sys.argv
    try:
        sys.argv = [_PROGRAM_NAME, *argv]
        result = _cli_main()
    finally:
        sys.argv = saved_argv

    if result is None:
        return 0
    return int(result)


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
