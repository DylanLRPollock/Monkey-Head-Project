from __future__ import annotations

from scripts.repo.audit_v120_assets import (
    build_report,
    classify_path,
    find_version_drift,
    render_markdown,
)
from scripts.repo.check_canon_terms import _compile_rules


def test_classification_keeps_archive_out_of_active_surface() -> None:
    assert classify_path("src/huey/memory/PY/main.py")[0] == "archive_only"
    assert classify_path(".migration/inventory/files.txt")[0] == "archive_only"
    assert classify_path("platform/boot/pool/example.udeb")[0] == (
        "generated_or_release_payload"
    )
    assert classify_path("src/huey/connectors/pyhuey/app.py")[0] == "review_required"
    assert classify_path("src/huey/api.py")[0] == "active"


def test_old_active_master_plans_are_drift_but_archived_plans_are_not() -> None:
    paths = [
        "master-plan-v120.2.json",
        "master-plan-v120.1.json",
        "archives/master-plan-v101.1.json",
        "src/huey/memory/JSON/master-plan-v5.json",
    ]
    assert find_version_drift(paths) == ["master-plan-v120.1.json"]


def test_report_requires_the_v120_2_pair_and_lists_duplicates() -> None:
    report = build_report(
        [
            "README.md",
            "src/huey/api.py",
            "src/huey/services/api.py",
        ]
    )
    assert report["missing_canonical_files"] == ["master-plan-v120.2.json"]
    assert report["duplicate_basename_groups"] == {
        "api.py": ["src/huey/api.py", "src/huey/services/api.py"]
    }
    markdown = render_markdown(report)
    assert "v120.2 Repository Asset Audit" in markdown
    assert "`master-plan-v120.2.json`" in markdown


def test_canon_regexes_match_real_terms_not_literal_backslashes() -> None:
    rules = {rule.name: rule.pattern for rule in _compile_rules()}
    assert rules["huey-core-active"].search("Huey Core")
    assert rules["live-microphone-v1"].search("live microphone")
    assert rules["glab-nonexistent-system"].search("Glab")
    assert rules["vague-hueybrain-node-label"].search(
        "active Huey Brain V1 execution node"
    )
