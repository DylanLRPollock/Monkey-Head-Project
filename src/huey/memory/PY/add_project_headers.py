# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Automated header injection utility

"""Utility to add standardized Monkey Head Project headers to source files.

This script walks the repository and ensures that Python, shell, and batch
scripts include the project header block requested by the project authors.
It preserves shebang and encoding lines and avoids duplicating an existing
header if it is already present.
"""

from __future__ import annotations

import argparse
import itertools
import re
from pathlib import Path
from typing import Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]

HEADER_LINES_COMMON = (
    "Monkey Head Project",
    "By: Dylan L.R. Pollock",
    "www.dlrp.ca",
)

PYTHON_EXTENSIONS = {".py"}
SHELL_EXTENSIONS = {".sh"}
BATCH_EXTENSIONS = {".bat"}
TARGET_EXTENSIONS = PYTHON_EXTENSIONS | SHELL_EXTENSIONS | BATCH_EXTENSIONS


def humanize_path(path: Path) -> str:
    """Return a human friendly description for a file."""

    relative = path.relative_to(REPO_ROOT)
    parent = relative.parent.as_posix()
    stem = relative.stem

    if path.name == "__init__.py":
        if parent == ".":
            return "Root package initializer"
        return f"Package initializer for {parent}"

    if path.name == "__main__.py":
        if parent == ".":
            return "Package entry point"
        return f"Module entry point for {parent}"

    stem_text = re.sub(r"[-_]+", " ", stem).strip()
    stem_text = re.sub(r"\s+", " ", stem_text)
    stem_text = stem_text.title() if stem_text else relative.name

    if path.suffix in PYTHON_EXTENSIONS:
        description = f"{stem_text} module"
    elif path.suffix in SHELL_EXTENSIONS:
        description = f"{stem_text} shell script"
    elif path.suffix in BATCH_EXTENSIONS:
        description = f"{stem_text} batch script"
    else:
        description = stem_text

    if parent != ".":
        description = f"{description} ({parent})"

    return description


def build_header(path: Path) -> Sequence[str]:
    description = humanize_path(path)

    if path.suffix in BATCH_EXTENSIONS:
        prefix = "REM"
    else:
        prefix = "#"

    header = [f"{prefix} {line}" for line in HEADER_LINES_COMMON]
    header.append(f"{prefix} HueyOS: {description}")
    return header


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def write_lines(path: Path, lines: Iterable[str]) -> None:
    text = "\n".join(lines) + "\n"
    path.write_text(text, encoding="utf-8")


def has_header(lines: Sequence[str]) -> bool:
    prefixes = ("# Monkey Head Project", "REM Monkey Head Project")
    for line in itertools.islice(lines, 0, 10):
        stripped = line.strip()
        if any(stripped.startswith(prefix) for prefix in prefixes):
            return True
    return False


def insertion_index(path: Path, lines: Sequence[str]) -> int:
    idx = 0
    if lines and lines[0].startswith("#!"):
        idx += 1
    if path.suffix in PYTHON_EXTENSIONS and idx < len(lines):
        if re.match(r"#.*coding[:=]", lines[idx]):
            idx += 1
    return idx


def ensure_header(path: Path, dry_run: bool = False) -> bool:
    original_lines = read_lines(path)
    if has_header(original_lines):
        return False

    header_lines = build_header(path)
    idx = insertion_index(path, original_lines)

    updated_lines = list(original_lines)
    updated_lines[idx:idx] = header_lines + [""]

    if not dry_run:
        write_lines(path, updated_lines)
    return True


def find_targets(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in TARGET_EXTENSIONS:
            yield path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="Only report files missing headers"
    )
    parser.add_argument(
        "paths", nargs="*", type=Path, default=[REPO_ROOT], help="Paths to scan"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    modified_any = False
    missing: list[Path] = []

    for input_path in args.paths:
        root = (
            (REPO_ROOT / input_path).resolve()
            if not input_path.is_absolute()
            else input_path
        )
        if root.is_file():
            targets = [root]
        else:
            targets = list(find_targets(root))
        for path in targets:
            if args.check:
                if not has_header(read_lines(path)):
                    missing.append(path.relative_to(REPO_ROOT))
            else:
                if ensure_header(path):
                    modified_any = True

    if args.check:
        if missing:
            for path in missing:
                print(path)
            return 1
        return 0

    return 0 if modified_any else 1


if __name__ == "__main__":
    raise SystemExit(main())
