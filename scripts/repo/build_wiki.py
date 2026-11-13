#!/usr/bin/env python3
"""Generate and validate the complete v201.x Monkey-Head-Project GitHub Wiki."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(__file__).resolve().parent
DATE = "2026-07-17"
FRAMEWORK = "v201.x review / Pre-Release #4"
REPO = "https://github.com/DylanLRPollock/Monkey-Head-Project"
LINK_RE = re.compile(r"\[\[([^\]|#]+)")

SOURCES = "\n".join(
    (
        "## Repository sources",
        "",
        f"- [Main repository]({REPO})",
        f"- [README]({REPO}/blob/main/README.md)",
        "- [v201.x standardization plan]("
        f"{REPO}/blob/main/docs/architecture/v201.x-standardization-plan.md)",
        "- [v201.x migration matrix]("
        f"{REPO}/blob/main/docs/architecture/v201.x-migration-matrix.md)",
        "- [Human oversight checklist]("
        f"{REPO}/blob/main/docs/review/v201.x-human-oversight-checklist.md)",
        f"- [Security policy]({REPO}/blob/main/SECURITY.md)",
        "",
    )
)

TOPIC = {
    "network": (
        "Document actual interfaces, addresses, exposure, authentication, "
        "firewalling, degraded operation, logs, and rollback. Old private-address "
        "examples are lineage, not current configuration."
    ),
    "security": (
        "Apply least privilege, explicit human authority, secret-safe logging, "
        "revocation, rollback, safe failure, and coordinated vulnerability "
        "reporting. Delivery is never automatic authorization."
    ),
    "backup": (
        "A backup is not proven until restore is tested. Record scope, schedule, "
        "encryption, retention, checksums, ownership, off-device copies, restore "
        "steps, and the last successful recovery test."
    ),
    "model": (
        "Model and provider selection is task- and evidence-based. Record "
        "model/revision, source, license, checksum, compute path, quantization, "
        "quality, latency, cost, privacy, fallback, and failure behavior."
    ),
    "build": (
        "Use repository-declared Python 3.13 requirements, constraints, tests, "
        "and entry points. Keep changes scoped, preserve provenance, avoid "
        "secrets, and document validation and rollback."
    ),
    "release": (
        "A release needs exact commit and artifacts, checksums, inventory, "
        "provenance, supported platforms, validation, known limitations, "
        "install/upgrade steps, rollback, security notes, and support policy."
    ),
    "privacy": (
        "Keep credentials, private continuity material, personal data, "
        "unnecessary audio/video, and secret-bearing logs out of public "
        "artifacts. Public presentation does not replace repository security."
    ),
    "lineage": (
        "Preserve the historical record without allowing old hardware roles, "
        "software versions, diagrams, or target-state claims to silently "
        "override the current project."
    ),
    "hardware": (
        "Record exact model and revision, condition, firmware and boot state, "
        "power and thermal observations, assigned role, tests, photos, backup, "
        "recovery, and replacement information."
    ),
    "controller": (
        "Controllers are dedicated, replaceable external operator devices. "
        "Require image provenance, device credentials, revocation, safe failure, "
        "controlled update/rollback, recovery, and key custody."
    ),
    "governance": (
        "Governance remains doctrine or target architecture unless implemented "
        "authority is separately proven and explicitly activated. Dylan remains "
        "the present human canon authority."
    ),
    "evidence": (
        "Retain run/transaction IDs, UTC timestamps, actors, inputs and "
        "checksums where relevant, stages, versions, outputs, warnings, errors, "
        "recovery actions, and final status without secrets."
    ),
}


TOPIC_RULES = (
    (("network", "ssh", "remote"), "network"),
    (("security", "safety"), "security"),
    (("backup", "snapshot", "recovery"), "backup"),
    (("model", "llm", "ollama", "api", "external-service"), "model"),
    (
        ("build", "dev", "makefile", "systemd", "cli", "software-stack", "repository"),
        "build",
    ),
    (("release", "publishing"), "release"),
    (("privacy", "license", "provenance", "contributing", "style"), "privacy"),
    (
        (
            "history",
            "historical",
            "timeline",
            "predecessor",
            "v120",
            "v200",
            "migration",
        ),
        "lineage",
    ),
    (("hardware", "power", "thermal", "battery"), "hardware"),
    (("controller", "nexus"), "controller"),
    (
        ("governance", "citizen", "clause", "collective", "bifurcation", "decision"),
        "governance",
    ),
)


def topic_text(name: str) -> str:
    normalized = name.lower()
    for terms, topic in TOPIC_RULES:
        if any(term in normalized for term in terms):
            return TOPIC[topic]
    return TOPIC["evidence"]


def load_data():
    nav = json.loads((DATA / "wiki_legacy.json").read_text())
    specs = {}
    for path in sorted(DATA.glob("wiki_pages_*.json")):
        specs.update(json.loads(path.read_text()))
    return nav, specs


def generated_spec(name, category):
    title = name.replace("-", " ")
    return {
        "title": title,
        "category": category,
        "classification": "Explanatory current guide; evidence-gated",
        "summary": f"Complete v201.x guidance for {title.lower()}.",
        "body": f"""## Purpose

This page places **{title}** inside the current v201.x project model and
replaces unsupported assumptions from the 2025 wiki.

## Current rule

{topic_text(name)}

## Required record

- current truth classification;
- exact version, device, artifact, or interface identity;
- prerequisites and authority boundaries;
- expected and observed results;
- logs, checksums, screenshots, or photographs where useful;
- known limitations and failure behavior;
- rollback, recovery, replacement, or supersession condition.

## Related orientation

Read [[Current-Status]], [[Truth-Classes]],
[[Source-Authority-and-Documentation]], and [[Page-Index]].""",
        "sources": ["readme", "standardization", "migration"],
    }


def render(name, spec):
    return f"""# {spec['title']}

> [!IMPORTANT]
> **Status date:** {spec.get('status_date', DATE)} · **Framework:** {spec.get('framework', FRAMEWORK)} ·
> **Classification:** {spec['classification']} · **Authority:** explanatory
> wiki; accepted plans, merged implementation evidence, and tests determine
> current implementation status.

**Summary:** {spec['summary']}

{spec['body'].strip()}

{spec.get('source_links', SOURCES)}"""


def _expected_pages(nav, specs):
    groups = nav["sidebar_groups"]
    categories = {name: group for group, names in groups for name in names}
    expected = list(dict.fromkeys(name for _, names in groups for name in names))
    for name in expected:
        specs.setdefault(name, generated_spec(name, categories[name]))
    specs.setdefault("Page-Index", generated_spec("Page-Index", "History and lineage"))
    return groups, expected, specs


def _write_legacy_pages(output, nav, specs):
    for old, info in nav["legacy_pages"].items():
        if old in specs:
            continue
        body = (
            "# Historical or compatibility page\n\n"
            "> [!CAUTION]\n"
            f"> **Classification:** {info['classification']}. This page name "
            "comes from the 2025 wiki and is not current guidance.\n\n"
            f"{info['note']}\n\n"
            f"Continue to [[{info['target']}]]. See [[Historical-2025-Wiki]] "
            "and [[Wiki-Migration-Map]].\n"
        )
        (output / f"{old}.md").write_text(body, encoding="utf-8")


def _write_sidebar(output, groups, specs):
    side = ["- [[Home|Home]]"]
    for group, names in groups:
        side.append(f"- **{group}**")
        side.extend(f"  - [[{name}|{specs[name]['title']}]]" for name in names)
    (output / "_Sidebar.md").write_text("\n".join(side) + "\n", encoding="utf-8")


def _write_page_index(output, expected, specs):
    rows = "\n".join(
        f"- [[{name}|{specs[name]['title']}]] — {specs[name]['summary']}"
        for name in expected
    )
    page = output / "Page-Index.md"
    page.write_text(
        page.read_text() + "\n## Complete page list\n\n" + rows + "\n",
        encoding="utf-8",
    )


def _write_manifest(output, expected):
    files = []
    for path in sorted(output.glob("*.md")):
        data = path.read_bytes()
        files.append(
            {
                "file": path.name,
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
            }
        )
    manifest = {
        "status_date": DATE,
        "framework": FRAMEWORK,
        "current_pages": len(expected),
        "compatibility_pages": sum(
            1
            for path in output.glob("*.md")
            if path.stem not in expected and not path.name.startswith("_")
        ),
    }
    (output / "wiki-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    (output / "SHA256SUMS").write_text(
        "\n".join(f"{item['sha256']}  {item['file']}" for item in files) + "\n",
        encoding="utf-8",
    )
    return manifest


def build(output: Path):
    nav, specs = load_data()
    groups, expected, specs = _expected_pages(nav, specs)
    output.mkdir(parents=True, exist_ok=True)
    for path in output.iterdir():
        if path.is_file():
            path.unlink()
    for name in expected:
        (output / f"{name}.md").write_text(
            render(name, specs[name]).strip() + "\n", encoding="utf-8"
        )
    _write_page_index(output, expected, specs)
    _write_legacy_pages(output, nav, specs)
    _write_sidebar(output, groups, specs)
    (output / "_Footer.md").write_text(
        f"Monkey-Head-Project / HueyOS · Dylan L.R. Pollack · Updated {DATE}  \n"
        "Code: GPL-3.0-only · Documentation/media: CC-BY-SA-4.0 unless "
        "otherwise noted  \nThe wiki is explanatory; implementation evidence "
        "is authoritative.\n",
        encoding="utf-8",
    )
    validate(output, expected, nav)
    return _write_manifest(output, expected)


def _legacy_page_errors(names, expected, nav):
    errors = []
    for old, info in nav["legacy_pages"].items():
        if old not in names and old not in expected:
            errors.append(f"missing compatibility page {old}")
        if info["target"] not in names:
            errors.append(f"{old}: missing target {info['target']}")
    return errors


def _page_content_errors(output, names, expected):
    errors = []
    for page in output.glob("*.md"):
        text = page.read_text()
        if page.stem in expected and not re.search(r"\*\*Status date:\*\* \d{4}-\d{2}-\d{2}", text):
            errors.append(f"{page.name}: missing status date")
        errors.extend(
            f"{page.name}: unresolved [[{target}]]"
            for target in LINK_RE.findall(text)
            if target not in names
        )
    return errors


def validate(output, expected, nav):
    names = {p.stem for p in output.glob("*.md") if not p.name.startswith("_")}
    errors = [f"missing current page {name}" for name in expected if name not in names]
    errors.extend(_legacy_page_errors(names, expected, nav))
    errors.extend(_page_content_errors(output, names, expected))
    if len(expected) < 66:
        errors.append(f"only {len(expected)} current pages")
    if errors:
        raise SystemExit("Wiki validation failed:\n- " + "\n- ".join(errors))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("output", nargs="?", default="build/wiki")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    m = build(Path(args.output))
    if not args.check:
        print(
            f"Generated {m['current_pages']} current pages and "
            f"{m['compatibility_pages']} compatibility pages with manifest "
            "and checksums."
        )


if __name__ == "__main__":
    main()
