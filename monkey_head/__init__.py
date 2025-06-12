# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
"""Utilities exposed for convenient imports."""

from .formatter import format_text
from .gencore import generate_core_data
from . import subos_manager
from .logging_setup import configure_logging
from .utils.logger import get_logger
from .convert_png_to_jpeg import convert_png_to_jpeg

# Initialize project-wide logging as soon as the package is imported
configure_logging()

__all__ = [
    "format_text",
    "generate_core_data",
    "subos_manager",
    "get_logger",
    "convert_png_to_jpeg",
]
