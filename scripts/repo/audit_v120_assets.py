#!/usr/bin/env python3
"""Inventory repository assets against the v120.2 alignment policy.

This is intentionally a classification tool, not a deletion tool. It creates a
repeatable view of the repository so cleanup decisions can be reviewed before
files are moved or removed.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath
from typing import Iterable, Sequence

POLICY_VERSION = "120.2"
REQUIRED_CANONICAL_FILES = ("README.md", "master-plan-v120.2.json")


@dataclass(frozen=True)
class ClassificationRule:
    category: str
    prefixes: tuple[str, ...]
    reason: str


RULES: tuple[ClassificationRule, ...] = (
    ClassificationRule(
        "archive_only",
        (
            ".migration/",
            "archive/",
            "archives/",
            "docs/archive/",
            "docs/archives/",
            "src/huey/memory/",
            "src/huey/prompts/OLD/",
        ),
        "Historical evidence; not an active implementation or authority surface.",
    ),
    ClassificationRule(
        "generated_or_release_payload",
        (".disk/", "docs/_build/", "platform/boot/"),
        "Generated, packaged, or release-derived material; regenerate from source.",
    ),
    ClassificationRule(
        "vendored",
        ("vendor/",),
        "Third-party or upstream-derived code; preserve attribution and avoid direct edits.",
    ),
    ClassificationRule(
        "experimental",
        (
            "apps/huey-gui/",
            "src/huey/apps/command_center/",
            "src/huey/platform/windows/huey/",
        ),
        "Experimental GUI/Command Center surface; mock-first and non-operational.",
    ),
    ClassificationRule(
        "review_required",
        (
            "integrations/pygpt/",
            "src/huey/connectors/pyhuey/",
            "src/huey/pygpt_net/",
            "src/hueyos/",
            "scripts/automation/",
        ),
        "Known overlap, compatibility, or support-boundary area requiring reconciliation.",
    ),
)

_MASTER_PLAN_VERSION = re.compile(
    r"(?:master[-_]plan|master-plan)[^/]*?v(?P<version>\d+(?:\.\d+)?)",
    re.IGNORECASE,
)


def tracked_paths() -> list[str]:
    """Return NUL-safe tracked paths from the current Git worktree."""
    output = subprocess.check_output(
        ["git", "ls-files", "-z"],
        text=True,
        encoding="utf-8",
        errors="surrogateescape",
    )
    return sorted(path for path in output.split("\0") if path)


def read_inventory(path: str) -> list[str]:
    """Read a newline-delimited inventory snapshot."""
    with open(path, encoding="utf-8", errors="surrogateescape") as handle:
        return sorted(line.strip().strip('"') for line in handle if line.strip())


def normalize_repository_path(path: str) -> str:
    """Return one stable POSIX-style representation of a repository path."""
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def normalize_repository_paths(paths: Iterable[str]) -> list[str]:
    """Normalize and deduplicate paths while preserving deterministic order."""
    return sorted(
        {
            normalized
            for path in paths
            if (normalized := normalize_repository_path(path))
        }
    )


def classify_path(path: str) -> tuple[str, str]:
    """Classify one repository-relative path using first-match policy order."""
    normalized = normalize_repository_path(path)
    for rule in RULES:
        if any(normalized.startswith(prefix) for prefix in rule.prefixes):
            return rule.category, rule.reason
    return (
        "active",
        "Current-facing source, configuration, test, documentation, or repository tooling.",
    )


def find_version_drift(paths: Iterable[str]) -> list[str]:
    """Find current-facing master plans whose filename is not the canonical version."""
    findings: list[str] = []
    for path in normalize_repository_paths(paths):
        category, _ = classify_path(path)
        if category in {"archive_only", "generated_or_release_payload", "vendored"}:
            continue
        match = _MASTER_PLAN_VERSION.search(path)
        if match and match.group("version") != POLICY_VERSION:
            findings.append(path)
    return sorted(findings)


def duplicate_basenames(paths: Iterable[str]) -> dict[str, list[str]]:
    """Return duplicate basenames across active and review-required surfaces."""
    grouped: dict[str, list[str]] = defaultdict(list)
    for path in normalize_repository_paths(paths):
        category, _ = classify_path(path)
        if category not in {"active", "review_required", "experimental"}:
            continue
        grouped[PurePosixPath(path).name].append(path)
    return {
        name: sorted(locations)
        for name, locations in sorted(grouped.items())
        if len(locations) > 1
    }


def build_report(paths: Sequence[str]) -> dict[str, object]:
    """Build a deterministic, JSON-serializable v120.2 repository report."""
    normalized_paths = normalize_repository_paths(paths)
    categories = Counter(classify_path(path)[0] for path in normalized_paths)
    missing = [
        path for path in REQUIRED_CANONICAL_FILES if path not in normalized_paths
    ]
    duplicates = duplicate_basenames(normalized_paths)
    return {
        "policy_version": POLICY_VERSION,
        "tracked_path_count": len(normalized_paths),
        "category_counts": dict(sorted(categories.items())),
        "missing_canonical_files": missing,
        "current_facing_master_plan_version_drift": find_version_drift(
            normalized_paths
        ),
        "duplicate_basename_groups": duplicates,
        "duplicate_basename_group_count": len(duplicates),
        "rules": [asdict(rule) for rule in RULES],
    }


def render_markdown(report: dict[str, object]) -> str:
    """Render the report as a reviewable Markdown artifact."""
    lines = [
        f"# v{report['policy_version']} Repository Asset Audit",
        "",
        f"Tracked paths: **{report['tracked_path_count']}**",
        "",
        "## Classification counts",
        "",
        "| Classification | Paths |",
        "|---|---:|",
    ]
    counts = report["category_counts"]
    assert isinstance(counts, dict)
    lines.extend(f"| `{name}` | {count} |" for name, count in counts.items())

    lines.extend(["", "## Canonical file check", ""])
    missing = report["missing_canonical_files"]
    assert isinstance(missing, list)
    lines.append(
        "All required v120.2 files are present."
        if not missing
        else "Missing: " + ", ".join(f"`{path}`" for path in missing)
    )

    lines.extend(["", "## Current-facing master-plan filename drift", ""])
    drift = report["current_facing_master_plan_version_drift"]
    assert isinstance(drift, list)
    lines.extend(["None detected."] if not drift else [f"- `{path}`" for path in drift])

    lines.extend(["", "## Duplicate basenames", ""])
    lines.append(
        "Duplicate names are review candidates, not automatic deletion candidates."
    )
    duplicates = report["duplicate_basename_groups"]
    assert isinstance(duplicates, dict)
    for name, locations in duplicates.items():
        lines.extend(["", f"### `{name}`", ""])
        lines.extend(f"- `{path}`" for path in locations)

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inventory",
        help="Read paths from an existing newline-delimited inventory instead of Git.",
    )
    parser.add_argument(
        "--format", choices=("json", "markdown"), default="markdown"
    )
    parser.add_argument(
        "--fail-on-canon-drift",
        action="store_true",
        help="Return non-zero when required files are missing or old active plans remain.",
    )
    args = parser.parse_args()

    paths = read_inventory(args.inventory) if args.inventory else tracked_paths()
    report = build_report(paths)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_markdown(report), end="")

    has_drift = bool(report["missing_canonical_files"]) or bool(
        report["current_facing_master_plan_version_drift"]
    )
    return 1 if args.fail_on_canon_drift and has_drift else 0


if __name__ == "__main__":
    sys.exit(main())
