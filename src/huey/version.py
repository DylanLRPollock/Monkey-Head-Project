"""Version metadata for HueyOS and the speculative GenCore stack."""

from __future__ import annotations

from .constants import API_VERSION, APP_NAME

VERSION = "0.3.0"
KERNEL_CODENAME = "cloud-pyramid"


def version_payload() -> dict[str, str]:
    return {
        "application": APP_NAME,
        "version": VERSION,
        "api_version": API_VERSION,
        "kernel_codename": KERNEL_CODENAME,
    }


__all__ = ["API_VERSION", "KERNEL_CODENAME", "VERSION", "version_payload"]
