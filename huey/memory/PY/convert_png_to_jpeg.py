# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Convert Png To Jpeg module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
"""Utility to convert PNG images to JPEG format."""

from __future__ import annotations

import os

from PIL import Image


def convert_png_to_jpeg(png_file: str, output_file: str, quality: int = 85) -> None:
    """Convert a PNG image to JPEG.

    Args:
        png_file: Path to the input PNG file.
        output_file: Path where the JPEG file will be saved.
        quality: JPEG quality 1-95 (default 85).

    Raises:
        FileNotFoundError: If ``png_file`` does not exist.
        OSError: If an image read/write error occurs.
    """
    if not os.path.exists(png_file):
        raise FileNotFoundError(f"PNG file '{png_file}' not found.")

    try:
        with Image.open(png_file) as img:
            if img.mode in ("RGBA", "LA"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.getchannel("A"))
                img = background
            else:
                img = img.convert("RGB")
            img.save(output_file, "JPEG", quality=quality)
    except OSError as e:
        raise OSError(f"Error converting '{png_file}' to JPEG: {e}")

    print(f"PNG converted to JPEG and saved to '{output_file}'")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert a PNG image to JPEG.")
    parser.add_argument("png_file", help="Path to the input PNG file.")
    parser.add_argument("output_file", help="Path to the output JPEG file.")
    parser.add_argument(
        "--quality",
        type=int,
        default=85,
        help="JPEG quality from 1 (worst) to 95 (best).",
    )
    args = parser.parse_args()

    try:
        convert_png_to_jpeg(args.png_file, args.output_file, args.quality)
    except Exception as e:
        print(f"Error: {e}")
