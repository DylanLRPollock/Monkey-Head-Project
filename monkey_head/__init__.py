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
from .logging_setup import configure_logging
from .utils.logger import get_logger
from .utils.sorting import list_files_by_mtime, natural_sort
import importlib
import os

LIGHT_IMPORTS = bool(os.environ.get("MONKEY_HEAD_LIGHT_IMPORTS"))

_lazy_modules = {
    "subos_manager": "monkey_head.subos_manager",
}

_lazy_functions = {
    "convert_png_to_jpeg": ("monkey_head.convert_png_to_jpeg", "convert_png_to_jpeg"),
    "pdf_pre_digestion": ("monkey_head.pdf_pre_digestion", "pdf_pre_digestion"),
    "convert_audio": ("monkey_head.media_conversion", "convert_audio"),
    "convert_video": ("monkey_head.media_conversion", "convert_video"),
    "convert_file": ("monkey_head.media_conversion", "convert_file"),
    "extract_audio": ("monkey_head.media_conversion", "extract_audio"),
    "convert_media": ("monkey_head.media_conversion", "convert_media"),
    "list_available_pdfs": ("monkey_head.pdf_utils", "list_available_pdfs"),
    "load_pdf_pages": ("monkey_head.pdf_chat", "load_pdf_pages"),
    "answer_question": ("monkey_head.pdf_chat", "answer_question"),
    "chat_with_pdf": ("monkey_head.pdf_chat", "chat_with_pdf"),
    "train_from_chat_and_pdfs": ("monkey_head.chat_learning", "train_from_chat_and_pdfs"),
    "train_from_project_sources": ("monkey_head.tensorflow_feed", "train_from_project_sources"),
}

_light_skip = {"subos_manager", "train_from_chat_and_pdfs", "train_from_project_sources"}


def __getattr__(name: str):
    """Lazy-load optional modules and functions."""
    if name in _lazy_modules:
        if LIGHT_IMPORTS and name in _light_skip:
            return None
        try:
            module = importlib.import_module(_lazy_modules[name])
        except Exception:  # pragma: no cover - optional dependency
            value = None
        else:
            value = module
        globals()[name] = value
        return value
    if name in _lazy_functions:
        if LIGHT_IMPORTS and name in _light_skip:
            return None
        module_name, attr = _lazy_functions[name]
        try:
            module = importlib.import_module(module_name)
            value = getattr(module, attr)
        except Exception:  # pragma: no cover - optional dependency
            value = None
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


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
    "extract_audio",
    "convert_media",
    "list_files_by_mtime",
    "natural_sort",
    "train_from_chat_and_pdfs",
    "train_from_project_sources",
    "list_available_pdfs",
    "load_pdf_pages",
    "answer_question",
    "chat_with_pdf",
]
