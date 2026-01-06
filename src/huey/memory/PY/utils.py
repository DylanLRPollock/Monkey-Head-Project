# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Utils module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
# huey/utils.py

import logging
from pathlib import Path
from typing import Iterable, Optional

from .exceptions import InvalidInputError

# Supported image formats for conversion
SUPPORTED_FORMATS: Iterable[str] = (
    "JPEG",
    "PNG",
    "BMP",
    "GIF",
    "TIFF",
    "WEBP",
)


def _load_image_module():
    from PIL import Image

    return Image


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

    Image = _load_image_module()
    with Image.open(jpeg_file) as img:
        img.save(png_file, format="PNG")

    return str(png_file)


def convert_image(
    image_path: str,
    output_format: str,
    output_path: Optional[str] | None = None,
    quality: int = 100,
) -> str:
    """Convert an image to a different format with maximum quality.

    Parameters
    ----------
    image_path : str
        Path to the source image.
    output_format : str
        Desired output format (e.g. ``"PNG"`` or ``"JPEG"``).
    output_path : str, optional
        Desired output path. Defaults to the same base name with a new extension.
    quality : int, optional
        Output quality for formats that support it. Defaults to ``100``.

    Returns
    -------
    str
        Path to the converted image.
    """

    img_file = Path(image_path)
    if not img_file.is_file():
        raise FileNotFoundError(f"{image_path} does not exist")

    fmt = output_format.upper()
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format: {output_format}")

    if output_path is None:
        suffix = ".jpg" if fmt == "JPEG" else f".{fmt.lower()}"
        out_file = img_file.with_suffix(suffix)
    else:
        out_file = Path(output_path)

    Image = _load_image_module()
    with Image.open(img_file) as img:
        save_kwargs = {}
        if fmt == "JPEG" or fmt == "WEBP":
            save_kwargs["quality"] = quality
        if fmt == "PNG":
            save_kwargs["optimize"] = True
        img.save(out_file, format=fmt, **save_kwargs)

    return str(out_file)


def convert_images_in_directory(
    directory: str,
    output_format: str,
    output_directory: Optional[str] | None = None,
    quality: int = 100,
) -> list[str]:
    """Convert all images in a directory to the specified format.

    Parameters
    ----------
    directory : str
        Directory containing images to convert.
    output_format : str
        Desired output format.
    output_directory : str, optional
        Directory to save converted images. Defaults to ``directory``.
    quality : int, optional
        Quality used for conversion. Defaults to ``100``.

    Returns
    -------
    list[str]
        Paths to converted images.
    """

    dir_path = Path(directory)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"{directory} is not a directory")

    out_dir = Path(output_directory) if output_directory else dir_path
    out_dir.mkdir(parents=True, exist_ok=True)

    converted_paths = []
    for file in dir_path.iterdir():
        if file.is_file():
            try:
                out_name = file.stem + (
                    ".jpg"
                    if output_format.upper() == "JPEG"
                    else f".{output_format.lower()}"
                )
                new_path = convert_image(
                    str(file),
                    output_format,
                    str(out_dir / out_name),
                    quality,
                )
                converted_paths.append(new_path)
            except (ValueError, FileNotFoundError):
                continue

    return converted_paths
