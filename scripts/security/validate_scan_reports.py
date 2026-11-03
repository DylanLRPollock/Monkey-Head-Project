"""Validate security scan artifacts so missing or broken scans fail CI.

Findings can remain advisory, but a missing, empty, or malformed report
must never be confused with a completed security scan.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class ReportValidationError(ValueError):
    """Security report could not be validated."""


def _read_report(path: Path) -> dict[str, Any]:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReportValidationError(f"Cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(report, dict):
        raise ReportValidationError("Security report must be a JSON object")
    return report


def validate_trivy_sarif(path: Path) -> int:
    """Return the number of findings in a valid Trivy SARIF 2.1.0 report."""
    report = _read_report(path)
    if report.get("version") != "2.1.0":
        raise ReportValidationError("Trivy report must use SARIF version 2.1.0")

    runs = report.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ReportValidationError("Trivy SARIF must contain at least one run")

    findings = 0
    for run in runs:
        if not isinstance(run, dict):
            raise ReportValidationError("Trivy SARIF run must be an object")
        tool = run.get("tool")
        if not isinstance(tool, dict):
            raise ReportValidationError("Trivy SARIF run has no tool metadata")
        driver = tool.get("driver")
        if not isinstance(driver, dict):
            raise ReportValidationError("Trivy SARIF run has no tool driver")
        name = driver.get("name")
        if not isinstance(name, str) or "trivy" not in name.lower():
            raise ReportValidationError("SARIF must identify the Trivy scanner")
        results = run.get("results", [])
        if not isinstance(results, list) or any(
            not isinstance(result, dict) for result in results
        ):
            raise ReportValidationError("Trivy SARIF results must be a list of objects")
        findings += len(results)
    return findings


def validate_bandit_report(path: Path) -> int:
    """Return findings from a valid Bandit report with a nonempty scan scope."""
    report = _read_report(path)
    results = report.get("results")
    errors = report.get("errors")
    if not isinstance(results, list) or not isinstance(errors, list):
        raise ReportValidationError("Bandit report requires results and errors lists")
    if errors:
        raise ReportValidationError(f"Bandit reported scan errors: {errors!r}")
    if any(not isinstance(result, dict) for result in results):
        raise ReportValidationError("Bandit results must contain only objects")

    metrics = report.get("metrics")
    totals = metrics.get("_totals") if isinstance(metrics, dict) else None
    scanned_lines = totals.get("loc") if isinstance(totals, dict) else None
    if not isinstance(scanned_lines, (int, float)) or scanned_lines <= 0:
        raise ReportValidationError("Bandit scanned no source lines")
    return len(results)


def validate_pip_audit_report(path: Path) -> int:
    """Return vulnerability count from a populated pip-audit JSON report."""
    report = _read_report(path)
    dependencies = report.get("dependencies")
    if not isinstance(dependencies, list) or not dependencies:
        raise ReportValidationError("pip-audit must report installed dependencies")

    vulnerabilities = 0
    for dependency in dependencies:
        if not isinstance(dependency, dict):
            raise ReportValidationError("pip-audit dependency must be an object")
        if not isinstance(dependency.get("name"), str) or not dependency["name"]:
            raise ReportValidationError("pip-audit dependency is missing its name")
        # pip-audit may report version=null for installed distributions
        # whose metadata has no usable version; the audit still ran.
        version = dependency.get("version")
        if version is not None and (not isinstance(version, str) or not version):
            raise ReportValidationError("pip-audit dependency has an invalid version")
        vulns = dependency.get("vulns")
        if not isinstance(vulns, list):
            # pip-audit --skip-editable marks the local editable distribution
            # with a skip_reason instead of a version and vulnerabilities.
            # This narrowly allows that one documented local package.
            if (
                dependency["name"] == "hueyos"
                and version is None
                and dependency.get("skip_reason") == "distribution marked as editable"
                and "vulns" not in dependency
            ):
                continue
            raise ReportValidationError(
                "pip-audit dependency lacks a vulnerabilities list"
            )
        if "skip_reason" in dependency:
            raise ReportValidationError(
                "pip-audit dependency cannot be both audited and skipped"
            )
        if any(not isinstance(vuln, dict) for vuln in vulns):
            raise ReportValidationError("pip-audit vulnerability must be an object")
        vulnerabilities += len(vulns)
    return vulnerabilities


VALIDATORS = {
    "trivy": validate_trivy_sarif,
    "bandit": validate_bandit_report,
    "pip-audit": validate_pip_audit_report,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scanner", choices=sorted(VALIDATORS))
    parser.add_argument("report", type=Path)
    args = parser.parse_args(argv)

    try:
        findings = VALIDATORS[args.scanner](args.report)
    except ReportValidationError as exc:
        parser.exit(1, f"Invalid {args.scanner} security report: {exc}\n")
    print(f"{args.scanner} report validated ({findings} findings)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
