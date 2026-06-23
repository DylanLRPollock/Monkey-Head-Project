"""Compatibility wrapper for :mod:`huey.media.convert_png_to_jpeg`."""

from huey.media.convert_png_to_jpeg import *  # noqa: F401,F403
from huey.media.convert_png_to_jpeg import main

if __name__ == "__main__":
    raise SystemExit(main())
