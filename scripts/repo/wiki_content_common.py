"""Content registry for the Monkey-Head-Project GitHub Wiki.

This module intentionally contains explanatory wiki prose rather than runtime logic.
The generator in ``build_wiki.py`` adds common status/source blocks, validates links,
and materializes the separate GitHub Wiki repository.
"""

from __future__ import annotations

STATUS_DATE = "2026-07-17"
FRAMEWORK = "v201.x review / Pre-Release #4"
PROJECT = "Monkey-Head-Project / HueyOS"

SOURCES = {
    "repository": ("Main repository", "https://github.com/DylanLRPollock/Monkey-Head-Project"),
    "readme": ("README — v201.x repository front door", "https://github.com/DylanLRPollock/Monkey-Head-Project/blob/main/README.md"),
    "standardization": ("v201.x standardization plan", "https://github.com/DylanLRPollock/Monkey-Head-Project/blob/main/docs/architecture/v201.x-standardization-plan.md"),
    "migration": ("v201.x migration matrix", "https://github.com/DylanLRPollock/Monkey-Head-Project/blob/main/docs/architecture/v201.x-migration-matrix.md"),
    "oversight": ("v201.x human-oversight checklist", "https://github.com/DylanLRPollock/Monkey-Head-Project/blob/main/docs/review/v201.x-human-oversight-checklist.md"),
    "controller": ("HueyNexusController specification", "https://github.com/DylanLRPollock/Monkey-Head-Project/blob/main/docs/hardware/huey-nexus-controller.md"),
    "controller_json": ("HueyNexusController machine-readable specification", "https://github.com/DylanLRPollock/Monkey-Head-Project/blob/main/docs/hardware/huey-nexus-controller.json"),
    "security": ("Security policy", "https://github.com/DylanLRPollock/Monkey-Head-Project/blob/main/SECURITY.md"),
    "provenance": ("Provenance and license boundaries", "https://github.com/DylanLRPollock/Monkey-Head-Project/blob/main/docs/legal/provenance-and-licenses.md"),
    "master_v1203": ("Accepted predecessor master plan v120.3", "https://github.com/DylanLRPollock/Monkey-Head-Project/blob/main/master-plan-v120.3.json"),
    "master_v201": ("Candidate master plan v201.0", "https://github.com/DylanLRPollock/Monkey-Head-Project/blob/main/master-plan-v201.0-candidate.json"),
    "pyproject": ("Python package metadata", "https://github.com/DylanLRPollock/Monkey-Head-Project/blob/main/pyproject.toml"),
    "forward_v1203": ("v120.3 forward-path decision record", "https://github.com/DylanLRPollock/Monkey-Head-Project/blob/main/docs/architecture/v120.3-forward-path-decision-record.md"),
    "wiki_audit": ("GitHub Wiki overhaul record", "https://github.com/DylanLRPollock/Monkey-Head-Project/blob/main/docs/wiki-overhaul-v201.md"),
}


def spec(
    title: str,
    category: str,
    classification: str,
    summary: str,
    body: str,
    sources: tuple[str, ...],
) -> dict[str, object]:
    return {
        "title": title,
        "category": category,
        "classification": classification,
        "summary": summary,
        "body": body.strip(),
        "sources": sources,
    }

