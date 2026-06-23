#!/usr/bin/env python3
"""Check for newly-added repository drift strings in current-facing content."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class DriftRule:
    name: str
    pattern: re.Pattern[str]
    message: str
    strict: bool = True


STRICT_CURRENT_FACING_PREFIXES: tuple[str, ...] = (
    "README",
    "docs/",
    ".github/",
    "infra/",
    "src/huey/connectors/",
    "src/huey/platform/",
    "scripts/",
    "Makefile",
    "Dockerfile",
)

NON_CURRENT_FACING_PREFIXES: tuple[str, ...] = (
    "archive/",
    "archives/",
    "docs/archive/",
    "docs/archives/",
    "docs/audits/",
    "docs/provenance/",
    "provenance/",
    "vendor/",
    "tests/fixtures/",
)

NON_CURRENT_FACING_NAMES: tuple[str, ...] = (
    "CHANGELOG.md",
    "LICENSE",
    "scripts/repo/check_repo_drift.py",
)


def _is_pyhuey_canonical() -> bool:
    return os.path.isdir("src/huey/connectors/pyhuey")


RULES: list[DriftRule] = [
    DriftRule(
        name="repo-py-gpt-path",
        pattern=re.compile(r"\brepo/py-gpt\b"),
        message=(
            "Replace stale path 'repo/py-gpt' with current pathing "
            "(for example src/huey/connectors/pyhuey)."
        ),
    ),
    DriftRule(
        name="windows-hueybody-path",
        pattern=re.compile(r"\bplatform/windows/hueybody\b"),
        message="Use src/huey/platform/windows/huey for cockpit/build paths.",
    ),
    DriftRule(
        name="huey-core-label",
        pattern=re.compile(r"\bHuey Core\b"),
        message=(
            "Use 'Huey Body' for current-facing docs, keeping Huey Core only "
            "for archive/provenance contexts."
        ),
    ),
    DriftRule(
        name="docker-primary-pygpt",
        pattern=re.compile(r"\b(pygpt|pygpt-net)\b", re.IGNORECASE),
        message=(
            "Do not present PyGPT as the primary runtime in main Dockerfiles; "
            "use hueyos/HueyOS runtime entrypoints."
        ),
    ),
]


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


def is_current_facing(path: str) -> bool:
    if path in NON_CURRENT_FACING_NAMES:
        return False
    if any(path.startswith(prefix) for prefix in NON_CURRENT_FACING_PREFIXES):
        return False
    return any(path.startswith(prefix) for prefix in STRICT_CURRENT_FACING_PREFIXES)


def should_check_rule(path: str, rule: DriftRule) -> bool:
    if not is_current_facing(path):
        return False
    if rule.name == "docker-primary-pygpt":
        return os.path.basename(path) == "Dockerfile"
    if rule.name == "huey-core-label":
        return path.endswith(".md")
    if rule.name == "repo-py-gpt-path":
        return True
    if rule.name == "windows-hueybody-path":
        return True
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", help="Git base ref/commit to diff against")
    args = parser.parse_args()

    rules = list(RULES)
    if _is_pyhuey_canonical():
        rules.append(
            DriftRule(
                name="integrations-pygpt-path",
                pattern=re.compile(r"\bintegrations/pygpt\b"),
                message="Use src/huey/connectors/pyhuey as the canonical connector path.",
            )
        )

    base_ref = resolve_base_ref(args.base)
    strict_violations: list[str] = []
    warnings: list[str] = []

    for path, line, line_number in iter_added_lines(base_ref):
        for rule in rules:
            if not should_check_rule(path, rule):
                continue
            if rule.pattern.search(line):
                entry = f"{path}:{line_number}: {rule.message}"
                if rule.strict:
                    strict_violations.append(entry)
                else:
                    warnings.append(entry)

    if warnings:
        print("Repo drift warnings:")
        for warning in warnings:
            print(f"- {warning}")

    if strict_violations:
        print("Repo drift check failed with strict current-facing violations:")
        for violation in strict_violations:
            print(f"- {violation}")
        return 1

    print("Repo drift check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
