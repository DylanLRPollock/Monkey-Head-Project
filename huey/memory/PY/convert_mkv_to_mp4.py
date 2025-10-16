# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Convert Mkv To Mp4 module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
"""Utility to convert MKV video files to MP4 using ffmpeg."""

from __future__ import annotations

import os
import subprocess


def convert_mkv_to_mp4(mkv_file: str, output_file: str) -> None:
    """Convert an MKV video to MP4 without re-encoding.

    Parameters
    ----------
    mkv_file : str
        Path to the input MKV file.
    output_file : str
        Path where the MP4 file will be saved.
    """
    if not os.path.exists(mkv_file):
        raise FileNotFoundError(f"MKV file '{mkv_file}' not found.")

    cmd = ["ffmpeg", "-y", "-i", mkv_file, "-c", "copy", "-map", "0", output_file]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode("utf-8", "ignore"))

    print(f"MKV converted to MP4 and saved to '{output_file}'")


if __name__ == "__main__":  # pragma: no cover - CLI helper
    import argparse

    parser = argparse.ArgumentParser(description="Convert an MKV video to MP4.")
    parser.add_argument("mkv_file", help="Path to the input MKV file.")
    parser.add_argument("output_file", help="Path to the output MP4 file.")
    args = parser.parse_args()

    try:
        convert_mkv_to_mp4(args.mkv_file, args.output_file)
    except Exception as e:  # pragma: no cover - CLI exception handling
        print(f"Error: {e}")
