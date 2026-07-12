#!/usr/bin/env python3
"""Fail CI when active code adds legacy hueyos imports or module paths.

Canonical imports should use huey.os. The src/hueyos package remains only as a
temporary compatibility shim during the migration window.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*from\s+hueyos\b"),
    re.compile(r"^\s*import\s+hueyos\b"),
    re.compile(r"import_module\(\s*['\"]hueyos(\.|['\"])"),
    re.compile(r"['\"]hueyos\.[^'\"]+['\"]"),
    re.compile(r"\b-m\s+hueyos\."),
    re.compile(r"\bsrc/hueyos\b"),
)

ALLOWED_PATHS: set[str] = {
    "src/hueyos/__init__.py",
    "src/huey/hardware/plugins.py",
    "tests/test_hueyos_namespace.py",
    "tests/test_layout_canonicalization.py",
    "tests/test_v120_asset_audit.py",
    "scripts/repo/check_legacy_hueyos_imports.py",
    "docs/architecture/huey-layout.md",
}

# Audit policy must be able to name the compatibility namespace it measures.
# Keep this exact-line allowance narrower than exempting the whole audit file.
ALLOWED_TEXT_REFERENCES: set[tuple[str, str]] = {
    ("scripts/repo/audit_v120_assets.py", '"src/hueyos/",'),
}

ACTIVE_PATH_PREFIXES: tuple[str, ...] = (
    "src/",
    "tests/",
    "scripts/",
    ".github/",
    "infra/",
    "docs/architecture/",
)

ACTIVE_PATHS: set[str] = {
    "README.md",
    "Makefile",
    "conftest.py",
}

EXCLUDED_PATH_PREFIXES: tuple[str, ...] = (
    "src/huey/memory/ARCHIVE/",
    "src/huey/memory/MD/",
)

TEXT_SUFFIXES: tuple[str, ...] = (
    ".py",
    ".md",
    ".rst",
    ".txt",
    ".toml",
    ".yml",
    ".yaml",
    ".json",
    ".sh",
    ".ps1",
    ".bat",
)


def safe_print(message: str) -> None:
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    sys.stdout.buffer.write(f"{message}\n".encode(encoding, errors="replace"))


def git_ls_files() -> list[Path]:
    output = subprocess.check_output(["git", "ls-files"], text=True)
    return [Path(line.strip()) for line in output.splitlines() if line.strip()]


def should_scan(path: Path) -> bool:
    normalized = path.as_posix()
    if normalized in ALLOWED_PATHS:
        return False
    if any(normalized.startswith(prefix) for prefix in EXCLUDED_PATH_PREFIXES):
        return False
    if normalized in ACTIVE_PATHS:
        return True
    if not any(normalized.startswith(prefix) for prefix in ACTIVE_PATH_PREFIXES):
        return False
    return path.suffix.lower() in TEXT_SUFFIXES or path.name in {
        "Makefile",
        "Dockerfile",
    }


def is_allowed_text_reference(path: Path, line: str) -> bool:
    """Return whether one exact policy reference is intentionally allowed."""
    return (path.as_posix(), line.strip()) in ALLOWED_TEXT_REFERENCES


def main() -> int:
    violations: list[str] = []

    for path in git_ls_files():
        if not should_scan(path):
            continue
        if not path.is_file():
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for line_number, line in enumerate(text.splitlines(), start=1):
            if is_allowed_text_reference(path, line):
                continue
            for pattern in PATTERNS:
                if pattern.search(line):
                    violations.append(
                        f"{path.as_posix()}:{line_number}: {line.strip()}"
                    )
                    break

    if violations:
        safe_print("Legacy hueyos import/path check failed.")
        safe_print(
            "Use huey.os for canonical code and keep hueyos only as the compatibility shim."
        )
        for violation in violations:
            safe_print(f"- {violation}")
        return 1

    safe_print("Legacy hueyos import/path check passed.")
    return 0


if __name__ == "__main__":
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(errors="backslashreplace")
    sys.exit(main())
