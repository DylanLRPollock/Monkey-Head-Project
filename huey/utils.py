# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
# huey/utils.py

import logging
from pathlib import Path
from typing import Optional

from PIL import Image

from .exceptions import InvalidInputError


def setup_logging(config):
    """Set up logging configuration based on the config dictionary."""
    level_name = config.get("logging", {}).get("level", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    log_file = config.get("logging", {}).get("file", "huey.log")

    logging.basicConfig(
        level=level,
        filename=log_file,
        filemode="a",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logging.info("Logging is set up.")


def calculate_sum(a, b):
    """Calculate the sum of two numbers."""
    return a + b


def validate_input(value, expected_type):
    """Validate that the input is of the expected type."""
    if not isinstance(value, expected_type):
        raise InvalidInputError(f"Expected {expected_type}, got {type(value)} instead.")
    return True


def convert_jpeg_to_png(jpeg_path: str, png_path: Optional[str] | None = None) -> str:
    """Convert a JPEG image to PNG format.

    Parameters
    ----------
    jpeg_path : str
        Path to the input JPEG file.
    png_path : str, optional
        Desired output path for the PNG file. Defaults to the same base name
        as ``jpeg_path`` with a ``.png`` extension.

    Returns
    -------
    str
        The path to the saved PNG image.
    """

    jpeg_file = Path(jpeg_path)
    if not jpeg_file.is_file():
        raise FileNotFoundError(f"{jpeg_path} does not exist")

    if png_path is None:
        png_file = jpeg_file.with_suffix(".png")
    else:
        png_file = Path(png_path)

    with Image.open(jpeg_file) as img:
        img.save(png_file, format="PNG")

    return str(png_file)
