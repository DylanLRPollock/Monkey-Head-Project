"""Content-type aware parser routing for the HueyOS data subsystem."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .pdf_parser import parse_pdf_bytes
from .text_parser import normalize_text, split_sentences, token_frequency


def parse_data(
    payload: bytes | str | dict[str, Any], *, source: str = ""
) -> dict[str, object]:
    if isinstance(payload, dict):
        return {"kind": "mapping", "data": dict(payload)}
    if isinstance(payload, bytes):
        suffix = Path(source).suffix.lower()
        if suffix == ".pdf":
            return {"kind": "pdf", **parse_pdf_bytes(payload)}
        text = payload.decode("utf-8", errors="ignore")
    else:
        text = payload

    normalized = normalize_text(text)
    if normalized.startswith("{") and normalized.endswith("}"):
        try:
            return {"kind": "json", "data": json.loads(normalized)}
        except json.JSONDecodeError:
            pass
    return {
        "kind": "text",
        "text": normalized,
        "sentences": split_sentences(normalized),
        "token_frequency": token_frequency(normalized),
    }


__all__ = ["parse_data"]
