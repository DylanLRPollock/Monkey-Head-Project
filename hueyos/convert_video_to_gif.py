"""Filesystem compatibility wrapper for legacy test loaders."""

from huey.media.convert_video_to_gif import *  # noqa: F401,F403
from huey.media.convert_video_to_gif import main

if __name__ == "__main__":
    raise SystemExit(main())
