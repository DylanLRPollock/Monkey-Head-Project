# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
"""Utilities exposed for convenient imports."""

from .formatter import format_text
from .gencore import generate_core_data
from . import subos_manager
from .logging_setup import configure_logging
from .utils.logger import get_logger
from .convert_png_to_jpeg import convert_png_to_jpeg

try:
    from .pdf_pre_digestion import pdf_pre_digestion
except Exception:  # pragma: no cover - optional dependency
    pdf_pre_digestion = None
from .media_conversion import (
    convert_audio,
    convert_video,
    convert_file,
)
import os

if os.environ.get("MONKEY_HEAD_LIGHT_IMPORTS"):
    train_from_chat_and_pdfs = None
    train_from_project_sources = None
else:
    from .chat_learning import train_from_chat_and_pdfs
    from .tensorflow_feed import train_from_project_sources

# Initialize project-wide logging as soon as the package is imported
configure_logging()

__all__ = [
    "format_text",
    "generate_core_data",
    "subos_manager",
    "get_logger",
    "convert_png_to_jpeg",
    "pdf_pre_digestion",
    "convert_audio",
    "convert_video",
    "convert_file",
    "train_from_chat_and_pdfs",
    "train_from_project_sources",
]
