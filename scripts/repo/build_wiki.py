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

SOURCES = """## Repository sources

- [Main repository]({r})
- [README]({r}/blob/main/README.md)
- [v201.x standardization plan]({r}/blob/main/docs/architecture/v201.x-standardization-plan.md)
- [v201.x migration matrix]({r}/blob/main/docs/architecture/v201.x-migration-matrix.md)
- [Human oversight checklist]({r}/blob/main/docs/review/v201.x-human-oversight-checklist.md)
- [Security policy]({r}/blob/main/SECURITY.md)
""".format(
    r=REPO
)

TOPIC = {
    "network": "Document actual interfaces, addresses, exposure, authentication, firewalling, degraded operation, logs, and rollback. Old private-address examples are lineage, not current configuratio[...]",
    "security": "Apply least privilege, explicit human authority, secret-safe logging, revocation, rollback, safe failure, and coordinated vulnerability reporting. Delivery is never automatic authoriz[...]",
    "backup": "A backup is not proven until restore is tested. Record scope, schedule, encryption, retention, checksums, ownership, off-device copies, restore steps, and the last successful recovery t[...]",
    "model": "Model and provider selection is task- and evidence-based. Record model/revision, source, license, checksum, compute path, quantization, quality, latency, cost, privacy, fallback, and fai[...]",
    "build": "Use repository-declared Python 3.13 requirements, constraints, tests, and entry points. Keep changes scoped, preserve provenance, avoid secrets, and document validation and rollback.",
    "release": "A release needs exact commit and artifacts, checksums, inventory, provenance, supported platforms, validation, known limitations, install/upgrade steps, rollback, security notes, and s[...]",
    "privacy": "Keep credentials, private continuity material, personal data, unnecessary audio/video, and secret-bearing logs out of public artifacts. Public presentation does not replace repository [...]",
    "lineage": "Preserve the historical record without allowing old hardware roles, software versions, diagrams, or target-state claims to silently override the current project.",
    "hardware": "Record exact model and revision, condition, firmware and boot state, power and thermal observations, assigned role, tests, photos, backup, recovery, and replacement information.",
    "controller": "Controllers are dedicated, replaceable external operator devices. Require image provenance, device credentials, revocation, safe failure, controlled update/rollback, recovery, and k[...]",
    "governance": "Governance remains doctrine or target architecture unless implemented authority is separately proven and explicitly activated. Dylan remains the present human canon authority.",
    "evidence": "Retain run/transaction IDs, UTC timestamps, actors, inputs and checksums where relevant, stages, versions, outputs, warnings, errors, recovery actions, and final status without secret[...]",
}


def topic_text(name: str) -> str:
    n = name.lower()
    if any(x in n for x in ("network", "ssh", "remote")):
        return TOPIC["network"]
    if any(x in n for x in ("security", "safety")):
        return TOPIC["security"]
    if any(x in n for x in ("backup", "snapshot", "recovery")):
        return TOPIC["backup"]
    if any(x in n for x in ("model", "llm", "ollama", "api", "external-service")):
        return TOPIC["model"]
    if any(x in n for x in ("build", "dev", "makefile", "systemd", "cli", "software-stack", "repository")):
        return TOPIC["build"]
    if any(x in n for x in ("release", "publishing")):
        return TOPIC["release"]
    if any(x in n for x in ("privacy", "license", "provenance", "contributing", "style")):
        return TOPIC["privacy"]
    if any(x in n for x in ("history", "historical", "timeline", "predecessor", "v120", "v200", "migration")):
        return TOPIC["lineage"]
    if any(x in n for x in ("hardware", "power", "thermal", "battery")):
        return TOPIC["hardware"]
    if any(x in n for x in ("controller", "nexus")):
        return TOPIC["controller"]
    if any(x in n for x in ("governance", "citizen", "clause", "collective", "bifurcation", "decision")):
        return TOPIC["governance"]
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

This page places **{title}** inside the current v201.x project model and replaces unsupported assumptions from the 2025 wiki.

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

Read [[Current-Status]], [[Truth-Classes]], [[Source-Authority-and-Documentation]], and [[Page-Index]].""",
        "sources": ["readme", "standardization", "migration"],
    }


def render(name, spec):
    return f"""# {spec['title']}

> [!IMPORTANT]
> **Status date:** {DATE} · **Framework:** {FRAMEWORK} · **Classification:** {spec['classification']} · **Authority:** explanatory wiki; accepted plans, merged implementation evidence, tests, [...]

**Summary:** {spec['summary']}

{spec['body'].strip()}

{SOURCES}"""


def build(output: Path):
    nav, specs = load_data()
    groups = nav["sidebar_groups"]
    categories = {name: group for group, names in groups for name in names}
    expected = []
    for _, names in groups:
        for name in names:
            if name not in expected:
                expected.append(name)
    for name in expected:
        specs.setdefault(name, generated_spec(name, categories[name]))
    specs.setdefault("Page-Index", generated_spec("Page-Index", "History and lineage"))
    output.mkdir(parents=True, exist_ok=True)
    for p in output.iterdir():
        if p.is_file():
            p.unlink()
    for name in expected:
        (output / f"{name}.md").write_text(render(name, specs[name]).strip() + "\n", encoding="utf-8")
    index = "\n".join(
        f"- [[{n}|{specs[n]['title']}]] — {specs[n]['summary']}" for n in expected
    )
    p = output / "Page-Index.md"
    t = p.read_text()
    p.write_text(t + "\n## Complete page list\n\n" + index + "\n", encoding="utf-8")
    for old, info in nav["legacy_pages"].items():
        if old in specs:
            continue
        target = info["target"]
        text = f"""# Historical or compatibility page

> [!CAUTION]
> **Classification:** {info['classification']}. This page name comes from the 2025 wiki and is not current guidance.

{info['note']}

Continue to [[{target}]]. See [[Historical-2025-Wiki]] and [[Wiki-Migration-Map]].
"""
        (output / f"{old}.md").write_text(text, encoding="utf-8")
    side = ["- [[Home|Home]]"]
    for group, names in groups:
        side.append(f"- **{group}**")
        side.extend(f"  - [[{n}|{specs[n]['title']}]]" for n in names)
    (output / "_Sidebar.md").write_text("\n".join(side) + "\n", encoding="utf-8")
    (output / "_Footer.md").write_text(
        f"Monkey-Head-Project / HueyOS · Dylan L.R. Pollock · Updated {DATE}  \nCode: GPL-3.0-only · Documentation/media: CC-BY-SA-4.0 unless otherwise noted  \nTh[...]",
        encoding="utf-8",
    )
    validate(output, expected, nav)
    files = []
    for p in sorted(output.glob("*.md")):
        b = p.read_bytes()
        files.append(
            {
                "file": p.name,
                "sha256": hashlib.sha256(b).hexdigest(),
                "bytes": len(b),
            }
        )
    manifest = {
        "status_date": DATE,
        "framework": FRAMEWORK,
        "current_pages": len(expected),
        "compatibility_pages": len(
            [p for p in output.glob("*.md") if p.stem not in expected and not p.name.startswith("_")]
        ),
    }
    (output / "wiki-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (output / "SHA256SUMS").write_text(
        "\n".join(f"{x['sha256']}  {x['file']}" for x in files) + "\n", encoding="utf-8"
    )
    return manifest


def validate(output, expected, nav):
    names = {p.stem for p in output.glob("*.md") if not p.name.startswith("_")}
    errors = []
    for name in expected:
        if name not in names:
            errors.append(f"missing current page {name}")
    for old, info in nav["legacy_pages"].items():
        if old not in names and old not in expected:
            errors.append(f"missing compatibility page {old}")
        if info["target"] not in names:
            errors.append(f"{old}: missing target {info['target']}")
    for p in output.glob("*.md"):
        text = p.read_text()
        if p.stem in expected and DATE not in text:
            errors.append(f"{p.name}: missing status date")
        for target in LINK_RE.findall(text):
            if target not in names:
                errors.append(f"{p.name}: unresolved [[{target}]]")
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
            f"Generated {m['current_pages']} current pages and {m['compatibility_pages']} compatibility pages with manifest and checksums."
        )


if __name__ == "__main__":
    main()
