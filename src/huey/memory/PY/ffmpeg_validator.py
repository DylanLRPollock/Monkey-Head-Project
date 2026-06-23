"""Compatibility wrapper for :mod:`huey.media.ffmpeg_validator`."""

from huey.media.ffmpeg_validator import *  # noqa: F401,F403
from huey.media.ffmpeg_validator import main

if __name__ == "__main__":
    raise SystemExit(main())
