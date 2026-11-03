"""Failure-mode regression tests for security scan report validation."""

from __future__ import annotations

import json

import pytest

from scripts.security.validate_scan_reports import (
    ReportValidationError,
    main,
    validate_bandit_report,
    validate_pip_audit_report,
    validate_trivy_sarif,
)


def _write(tmp_path, data):
    report = tmp_path / "scan.json"
    report.write_text(json.dumps(data), encoding="utf-8")
    return report


def test_trivy_accepts_empty_findings_when_scan_completed(tmp_path):
    data = {
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": "Trivy"}}, "results": []}],
    }
    assert validate_trivy_sarif(_write(tmp_path, data)) == 0


def test_trivy_counts_reported_findings(tmp_path):
    data = {
        "version": "2.1.0",
        "runs": [
            {"tool": {"driver": {"name": "Trivy"}}, "results": [{}, {}]},
        ],
    }
    assert validate_trivy_sarif(_write(tmp_path, data)) == 2


@pytest.mark.parametrize(
    "data",
    [
        {},
        [],
        {"version": "2.0.0", "runs": []},
        {"version": "2.1.0", "runs": []},
        {"version": "2.1.0", "runs": [{}]},
        {"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "Other"}}}]},
        {
            "version": "2.1.0",
            "runs": [{"tool": {"driver": {"name": "Trivy"}}, "results": {}}],
        },
        {
            "version": "2.1.0",
            "runs": [{"tool": {"driver": {"name": "Trivy"}}, "results": [None]}],
        },
    ],
)
def test_trivy_rejects_incomplete_or_fake_reports(tmp_path, data):
    with pytest.raises(ReportValidationError):
        validate_trivy_sarif(_write(tmp_path, data))


def test_trivy_rejects_missing_and_corrupt_files(tmp_path):
    with pytest.raises(ReportValidationError, match="Cannot read"):
        validate_trivy_sarif(tmp_path / "missing.sarif")
    corrupt = tmp_path / "corrupt.sarif"
    corrupt.write_text("{", encoding="utf-8")
    with pytest.raises(ReportValidationError, match="Cannot read"):
        validate_trivy_sarif(corrupt)


def test_bandit_accepts_scan_with_no_findings(tmp_path):
    data = {"results": [], "errors": [], "metrics": {"_totals": {"loc": 250}}}
    assert validate_bandit_report(_write(tmp_path, data)) == 0


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"results": [], "errors": [], "metrics": {"_totals": {"loc": 0}}},
        {"results": [], "errors": ["parse failed"], "metrics": {"_totals": {"loc": 5}}},
        {"results": {}, "errors": [], "metrics": {"_totals": {"loc": 5}}},
    ],
)
def test_bandit_rejects_empty_or_failed_scans(tmp_path, data):
    with pytest.raises(ReportValidationError):
        validate_bandit_report(_write(tmp_path, data))


def test_pip_audit_accepts_and_counts_vulnerabilities(tmp_path):
    data = {
        "dependencies": [
            {"name": "example", "version": "1.0", "vulns": [{"id": "TEST-1"}]},
            {"name": "another", "version": "2.0", "vulns": []},
        ],
    }
    assert validate_pip_audit_report(_write(tmp_path, data)) == 1


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"dependencies": []},
        {"dependencies": [{"name": "example", "version": "1.0"}]},
        {"dependencies": [{"name": "", "version": "1.0", "vulns": []}]},
        {"dependencies": [{"name": "example", "version": "", "vulns": []}]},
        {"dependencies": [{"name": "example", "version": "1", "vulns": "none"}]},
    ],
)
def test_pip_audit_rejects_incomplete_results(tmp_path, data):
    with pytest.raises(ReportValidationError):
        validate_pip_audit_report(_write(tmp_path, data))


def test_cli_rejects_invalid_artifact(tmp_path):
    with pytest.raises(SystemExit) as error:
        main(["trivy", str(tmp_path / "missing.sarif")])
    assert error.value.code == 1


def test_cli_accepts_valid_artifact(tmp_path, capsys):
    data = {
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": "Trivy"}}, "results": []}],
    }
    assert main(["trivy", str(_write(tmp_path, data))]) == 0
    assert "validated" in capsys.readouterr().out
