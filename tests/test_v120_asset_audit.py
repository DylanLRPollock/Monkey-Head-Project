from __future__ import annotations

import re
from pathlib import Path

from scripts.repo.audit_v120_assets import (
    build_report,
    classify_path,
    find_version_drift,
    normalize_repository_path,
    normalize_repository_paths,
    render_markdown,
)
from scripts.repo.check_canon_terms import _compile_rules
from scripts.repo.check_legacy_hueyos_imports import is_allowed_text_reference
from scripts.repo.check_repo_drift import DriftRule, should_check_rule


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
        r".\master-plan-v120.0.json",
        "archives/master-plan-v101.1.json",
        "src/huey/memory/JSON/master-plan-v5.json",
    ]
    assert find_version_drift(paths) == [
        "master-plan-v120.0.json",
        "master-plan-v120.1.json",
    ]


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


def test_report_normalizes_and_deduplicates_cross_platform_paths() -> None:
    report = build_report(
        [
            "./README.md",
            r".\master-plan-v120.2.json",
            r"src\huey\api.py",
            "./src/huey/api.py",
            "src/huey/services/api.py",
        ]
    )
    assert report["tracked_path_count"] == 4
    assert report["missing_canonical_files"] == []
    assert report["duplicate_basename_groups"] == {
        "api.py": ["src/huey/api.py", "src/huey/services/api.py"]
    }


def test_path_normalization_is_stable() -> None:
    assert normalize_repository_path(r".\src\huey\api.py") == "src/huey/api.py"
    assert normalize_repository_path("././README.md") == "README.md"
    assert normalize_repository_paths(
        ["./README.md", "README.md", r"src\huey\api.py"]
    ) == ["README.md", "src/huey/api.py"]


def test_canon_regexes_match_real_terms_not_literal_backslashes() -> None:
    rules = {rule.name: rule.pattern for rule in _compile_rules()}
    assert rules["huey-core-active"].search("Huey Core")
    assert rules["live-microphone-v1"].search("live microphone")
    assert rules["glab-nonexistent-system"].search("Glab")
    assert rules["vague-hueybrain-node-label"].search(
        "active Huey Brain V1 execution node"
    )


def test_asset_audit_can_name_review_paths_without_failing_drift() -> None:
    audit_path = "scripts/repo/audit_v120_assets.py"
    integration_rule = DriftRule(
        name="integrations-pygpt-path",
        pattern=re.compile(r"\bintegrations/pygpt\b"),
        message="canonical connector",
    )
    other_rule = DriftRule(
        name="repo-py-gpt-path",
        pattern=re.compile(r"\brepo/py-gpt\b"),
        message="stale path",
    )
    assert not should_check_rule(audit_path, integration_rule)
    assert should_check_rule(audit_path, other_rule)


def test_legacy_namespace_allowance_is_exact_and_audit_only() -> None:
    audit_path = Path("scripts/repo/audit_v120_assets.py")
    assert is_allowed_text_reference(audit_path, '    "src/hueyos/",')
    assert not is_allowed_text_reference(audit_path, "import hueyos")
    assert not is_allowed_text_reference(
        Path("scripts/new_runtime.py"), '"src/hueyos/",'
    )
