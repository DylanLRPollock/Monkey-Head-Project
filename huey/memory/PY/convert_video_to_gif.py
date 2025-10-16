# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Convert Video To Gif module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
"""Utility to convert video files to GIF using ffmpeg."""

from __future__ import annotations

import os
import subprocess


def convert_video_to_gif(video_file: str, output_file: str, fps: int = 10) -> None:
    """Convert a video file to GIF.

    Parameters
    ----------
    video_file : str
        Path to the input video file.
    output_file : str
        Path where the GIF will be saved.
    fps : int, optional
        Frames per second for the resulting GIF.
    """
    if not os.path.exists(video_file):
        raise FileNotFoundError(f"Video file '{video_file}' not found.")

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_file,
        "-vf",
        f"fps={fps},scale=320:-1:flags=lanczos",
        output_file,
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode("utf-8", "ignore"))

    print(f"Video converted to GIF and saved to '{output_file}'")


if __name__ == "__main__":  # pragma: no cover - CLI helper
    import argparse

    parser = argparse.ArgumentParser(description="Convert a video to GIF.")
    parser.add_argument("video_file", help="Path to the input video file.")
    parser.add_argument("output_file", help="Path to the output GIF file.")
    parser.add_argument(
        "--fps",
        type=int,
        default=10,
        help="Frames per second for the GIF.",
    )
    args = parser.parse_args()

    try:
        convert_video_to_gif(args.video_file, args.output_file, args.fps)
    except Exception as e:  # pragma: no cover - CLI exception handling
        print(f"Error: {e}")
