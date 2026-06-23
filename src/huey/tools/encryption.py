"""Encryption helpers backed by ``cryptography`` when available."""

from __future__ import annotations


class FernetVault:
    """Small wrapper around :class:`cryptography.fernet.Fernet`."""

    def __init__(self, key: bytes | None = None) -> None:
        try:
            from cryptography.fernet import Fernet
        except (
            ImportError
        ) as exc:  # pragma: no cover - dependency should exist in core env
            raise RuntimeError("cryptography is required for FernetVault") from exc
        self._fernet_cls = Fernet
        self.key = key or Fernet.generate_key()
        self._fernet = Fernet(self.key)

    def encrypt_text(self, text: str) -> str:
        return self._fernet.encrypt(text.encode("utf-8")).decode("utf-8")

    def decrypt_text(self, payload: str) -> str:
        return self._fernet.decrypt(payload.encode("utf-8")).decode("utf-8")


__all__ = ["FernetVault"]
