#!/usr/bin/env python3
"""Scan current-facing docs/metadata for canon drift terms."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ARCHIVE_SEGMENTS = {
    "archive",
    "archives",
    "provenance",
    "history",
    "historical",
    "legacy",
    "audit",
    "audits",
}

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__"}

PROVENANCE_MARKERS = (
    "upstream",
    "derived",
    "fork",
    "compat",
    "compatibility",
    "legacy",
    "archive",
    "provenance",
    "formerly",
    "historical",
    "renamed",
)


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern[str]
    message: str


def _compile_rules() -> tuple[Rule, ...]:
    return (
        Rule(
            "huey-core-active",
            re.compile(r"\\bHuey Core\\b"),
            (
                "'Huey Core' appears as a current-facing term; use Huey Body "
                "only in historical/provenance context."
            ),
        ),
        Rule(
            "windows-hueybody-path",
            re.compile(r"\\bplatform/windows/hueybody\\b", re.IGNORECASE),
            "Use src/huey/platform/windows/huey for cockpit/build path references.",
        ),
        Rule(
            "live-microphone-v1",
            re.compile(r"\\blive\\s+microphone\\b", re.IGNORECASE),
            "Do not present live microphone as active V1 feature.",
        ),
        Rule(
            "huey-body-v1-runtime",
            re.compile(
                r"\\bHuey Body\\b.*\\b(V1|runtime|compute|cognition|node)\\b|"
                r"\\b(V1|runtime|compute|cognition|node)\\b.*\\bHuey Body\\b",
                re.IGNORECASE,
            ),
            "Do not present Huey Body as V1 compute/cognition/runtime node.",
        ),
        Rule(
            "hims-active-runtime",
            re.compile(r"\\bHIMS\\b", re.IGNORECASE),
            "Do not present HIMS as an active runtime.",
        ),
    )


def _iter_targets() -> Iterable[Path]:
    roots = [Path("README.md"), Path("docs"), Path("pyproject.toml")]

    docker_files = [Path("Dockerfile"), Path("docker"), Path("docs/docker")]
    roots.extend(docker_files)

    website_docs = [Path("website/docs"), Path("website")]
    roots.extend(website_docs)

    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        if root.is_file():
            if root not in seen:
                seen.add(root)
                yield root
            continue

        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".svg"}:
                continue
            if path not in seen:
                seen.add(path)
                yield path


def _is_archival_path(path: Path) -> bool:
    return any(segment.lower() in ARCHIVE_SEGMENTS for segment in path.parts)


def _has_provenance_marker(line: str) -> bool:
    lowered = line.lower()
    return any(marker in lowered for marker in PROVENANCE_MARKERS)


def _should_flag_pygpt(line: str) -> bool:
    if not re.search(r"\\bPyGPT\\b", line):
        return False
    if re.search(r"\\bPyHuey\\b", line):
        return False
    if _has_provenance_marker(line):
        return False
    return True


def main() -> int:
    rules = _compile_rules()
    violations: list[str] = []

    for path in _iter_targets():
        if _is_archival_path(path):
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for lineno, line in enumerate(content.splitlines(), start=1):
            if _should_flag_pygpt(line):
                violations.append(
                    f"{path}:{lineno}: Use PyHuey as the active cockpit name; "
                    "keep PyGPT for provenance only."
                )

            for rule in rules:
                if rule.name == "huey-core-active" and _has_provenance_marker(line):
                    continue
                if rule.name == "hims-active-runtime" and _has_provenance_marker(line):
                    continue
                if rule.pattern.search(line):
                    violations.append(f"{path}:{lineno}: {rule.message}")

    if violations:
        print("Canon drift check failed:")
        for violation in violations:
            print(f"- {violation}")
        return 1

    print("Canon drift check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
