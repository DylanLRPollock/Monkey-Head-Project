"""Regression check: security runbooks must not contain literal API keys.

Tests do not print detected tokens or reveal credential text.
"""

from __future__ import annotations

import re
from pathlib import Path

SECURITY_DOCS = Path(__file__).resolve().parents[1] / "docs" / "security"
KEY_SHAPED = re.compile(r"\bsk-(?:[A-Za-z0-9_-]{20,})\b")


def test_security_runbooks_do_not_embed_api_key_values() -> None:
    offenders = [
        path.relative_to(SECURITY_DOCS).as_posix()
        for path in sorted(SECURITY_DOCS.rglob("*.md"))
        if KEY_SHAPED.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == [], "Credential-shaped values in: " + ", ".join(offenders)


def test_key_detector_only_matches_long_secret_like_strings() -> None:
    assert KEY_SHAPED.search("sk-" + ("a" * 35)) is not None
    assert KEY_SHAPED.search("sk-example") is None
    assert KEY_SHAPED.search("<REDACTED-CREDENTIAL>") is None
