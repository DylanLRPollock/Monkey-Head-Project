"""Compatibility wrapper for :mod:`huey.apps.command_center.seed`."""

from huey.apps.command_center.seed import *  # noqa: F401,F403
from huey.apps.command_center.seed import main

if __name__ == "__main__":
    raise SystemExit(main())
