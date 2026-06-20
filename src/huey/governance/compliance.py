"""Compliance checks derived from policy enforcement outcomes."""

from __future__ import annotations


class ComplianceChecker:
    """Summarize whether policy results satisfy deployment requirements."""

    def check(self, policy_result: dict[str, object]) -> dict[str, object]:
        violations = list(policy_result.get("violations", []))
        approved = bool(policy_result.get("approved"))
        return {
            "compliant": approved and not violations,
            "violation_count": len(violations),
            "rationale": policy_result.get("rationale", ""),
        }


__all__ = ["ComplianceChecker"]
