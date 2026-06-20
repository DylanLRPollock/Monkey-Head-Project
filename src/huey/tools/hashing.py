"""Hashing helpers for payload integrity checks."""

from __future__ import annotations

from hashlib import sha256


def sha256_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def fingerprint_mapping(payload: dict[str, object]) -> str:
    parts = [f"{key}={payload[key]!r}" for key in sorted(payload)]
    return sha256_text("|".join(parts))


__all__ = ["fingerprint_mapping", "sha256_text"]
