"""Compression helpers for the honeycomb storage subsystem."""

from __future__ import annotations

import base64
import zlib


def compress_text(text: str) -> str:
    compressed = zlib.compress(text.encode("utf-8"))
    return base64.b64encode(compressed).decode("ascii")


def decompress_text(payload: str) -> str:
    compressed = base64.b64decode(payload.encode("ascii"))
    return zlib.decompress(compressed).decode("utf-8")


__all__ = ["compress_text", "decompress_text"]
