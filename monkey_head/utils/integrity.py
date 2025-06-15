# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
"""Utilities for verifying file integrity."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable, Mapping


def sha256_digest(file_path: str | Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    path = Path(file_path)
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_checksums(checksums: Mapping[str | Path, str]) -> list[str]:
    """Check each path against its expected digest.

    Parameters
    ----------
    checksums:
        Mapping of file paths to expected SHA-256 digests.

    Returns
    -------
    list[str]
        A list of file paths that failed verification. The list is empty when
        all files match their expected digests.
    """
    failed: list[str] = []
    for path, expected in checksums.items():
        actual = sha256_digest(path)
        if actual != expected:
            failed.append(str(path))
    return failed


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Verify file checksums")
    parser.add_argument("manifest", help="JSON file of path -> sha256")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    data = json.loads(manifest_path.read_text())
    failures = verify_checksums(data)
    if failures:
        print("Integrity check failed:")
        for f in failures:
            print(f" - {f}")
    else:
        print("All files verified")
