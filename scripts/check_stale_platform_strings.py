#!/usr/bin/env python3
"""Fail CI when newly added stale platform strings appear in active paths."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from typing import Iterable

BANNED_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\btrixie\b", re.IGNORECASE),
    re.compile(r"\b6\.18\.2\b"),
    re.compile(r"\bhueyos-v1\b", re.IGNORECASE),
    re.compile(r"\bdebian\s+13\b", re.IGNORECASE),
)

APPROVED_PATH_PREFIXES: tuple[str, ...] = (
    "archives/",
    ".migration/",
    "tests/",
)

APPROVED_PATHS: tuple[str, ...] = (
    "docs/kernel-6.18.2-runbook.md",
    "docs/version-reference-classification.md",
    "src/huey/memory/PY/update_sources_to_trixie.py",
    "scripts/check_stale_platform_strings.py",
)


def run_git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def resolve_base_ref(explicit_base: str | None) -> str:
    if explicit_base:
        return explicit_base

    base_ref = os.getenv("GITHUB_BASE_REF")
    if base_ref:
        candidate = f"origin/{base_ref}"
        try:
            run_git("rev-parse", "--verify", candidate)
            return run_git("merge-base", "HEAD", candidate)
        except subprocess.CalledProcessError:
            pass

    try:
        return run_git("rev-parse", "HEAD~1")
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Unable to determine a diff base. Pass --base explicitly."
        ) from exc


def iter_added_lines(base_ref: str) -> Iterable[tuple[str, str, int]]:
    diff = run_git("diff", "--unified=0", "--no-color", f"{base_ref}...HEAD", "--")

    current_file: str | None = None
    current_line = 0

    for raw_line in diff.splitlines():
        if raw_line.startswith("+++ b/"):
            current_file = raw_line[6:]
            continue

        if raw_line.startswith("@@"):
            plus_segment = raw_line.split("+", 1)[1].split(" ", 1)[0]
            line_token = plus_segment.split(",", 1)[0]
            current_line = int(line_token)
            continue

        if raw_line.startswith("+") and not raw_line.startswith("+++") and current_file:
            yield current_file, raw_line[1:], current_line
            current_line += 1


def is_approved_path(path: str) -> bool:
    if path in APPROVED_PATHS:
        return True

    return any(path.startswith(prefix) for prefix in APPROVED_PATH_PREFIXES)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", help="Git base ref/commit to diff against")
    args = parser.parse_args()

    base_ref = resolve_base_ref(args.base)
    violations: list[str] = []

    for path, line, line_number in iter_added_lines(base_ref):
        if is_approved_path(path):
            continue

        for pattern in BANNED_PATTERNS:
            if pattern.search(line):
                violations.append(
                    f"{path}:{line_number}: found stale platform string ({pattern.pattern})"
                )
                break

    if violations:
        print("Stale platform string check failed. Move these references to approved legacy/archive paths:")
        for violation in violations:
            print(f"- {violation}")
        return 1

    print("Stale platform string check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
