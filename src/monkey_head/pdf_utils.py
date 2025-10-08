"""PDF helper functions used by the HueyOS API."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_impl = import_module("huey.pdf_utils")

__all__ = ["find_pdf", "list_available_pdfs"]

list_available_pdfs = getattr(_impl, "list_available_pdfs")
find_pdf = getattr(_impl, "find_pdf")


def __getattr__(name: str) -> Any:
    return getattr(_impl, name)


__doc__ = _impl.__doc__
