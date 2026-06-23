"""Filesystem compatibility wrapper for legacy test loaders."""

from huey.media.convert_mkv_to_mp4 import *  # noqa: F401,F403
from huey.media.convert_mkv_to_mp4 import main

if __name__ == "__main__":
    raise SystemExit(main())
