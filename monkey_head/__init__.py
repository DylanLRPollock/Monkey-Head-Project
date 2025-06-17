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
from .function_registry import register_function, list_functions, get_functions
from .gencore import generate_core_data
from .logging_setup import configure_logging
import os

if not os.environ.get("MONKEY_HEAD_LIGHT_IMPORTS"):
    try:
        from . import subos_manager
    except Exception:  # pragma: no cover - optional dependency
        subos_manager = None
else:
    subos_manager = None
from .utils.logger import get_logger

try:
    from .convert_png_to_jpeg import convert_png_to_jpeg
except Exception:  # pragma: no cover - optional dependency
    convert_png_to_jpeg = None
try:
    from .convert_mkv_to_mp4 import convert_mkv_to_mp4
except Exception:  # pragma: no cover - optional dependency
    convert_mkv_to_mp4 = None
try:
    from .convert_video_to_gif import convert_video_to_gif
except Exception:  # pragma: no cover - optional dependency
    convert_video_to_gif = None

try:
    from .pdf_pre_digestion import pdf_pre_digestion
except Exception:  # pragma: no cover - optional dependency
    pdf_pre_digestion = None
from .media_conversion import (
    convert_audio,
    convert_video,
    convert_file,
    extract_audio,
    convert_media,
)
from .honeycomb_storage import HoneycombStorage
from .cloud_pyramid import CloudPyramid
from .hardware_interface import (
    send_hostos,
    send_subos,
    send_nanoos,
)
from .utils.sorting import list_files_by_mtime, natural_sort
from .pdf_utils import list_available_pdfs
from .storage_management import StorageManager

try:
    from .pdf_chat import load_pdf_pages, answer_question, chat_with_pdf
except Exception:  # pragma: no cover - optional dependency
    load_pdf_pages = None
    answer_question = None
    chat_with_pdf = None

if os.environ.get("MONKEY_HEAD_LIGHT_IMPORTS"):
    train_from_chat_and_pdfs = None
    train_from_project_sources = None
else:
    try:  # pragma: no cover - optional dependency
        from .chat_learning import train_from_chat_and_pdfs
    except Exception:
        train_from_chat_and_pdfs = None
    try:  # pragma: no cover - optional dependency
        from .tensorflow_feed import train_from_project_sources
    except Exception:
        train_from_project_sources = None

# Initialize project-wide logging as soon as the package is imported
configure_logging()

__all__ = [
    "format_text",
    "generate_core_data",
    "subos_manager",
    "get_logger",
    "convert_png_to_jpeg",
    "convert_mkv_to_mp4",
    "convert_video_to_gif",
    "pdf_pre_digestion",
    "convert_audio",
    "convert_video",
    "convert_file",
    "extract_audio",
    "convert_media",
    "list_files_by_mtime",
    "natural_sort",
    "train_from_chat_and_pdfs",
    "train_from_project_sources",
    "list_available_pdfs",
    "StorageManager",
    "load_pdf_pages",
    "answer_question",
    "chat_with_pdf",
    "HoneycombStorage",
    "CloudPyramid",
    "send_hostos",
    "send_subos",
    "send_nanoos",
    "register_function",
    "list_functions",
    "get_functions",
]
