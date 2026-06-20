"""Policy enforcement for the Cloud Pyramid governance system."""

from __future__ import annotations

from .audit import AuditLog
from .constitution import HueyConstitution
from .rules import Rule, RuleEngine


class PolicyEnforcer:
    """Combine constitutional principles, rules, and audit logging."""

    def __init__(
        self,
        constitution: HueyConstitution | None = None,
        rules: RuleEngine | None = None,
        audit_log: AuditLog | None = None,
    ) -> None:
        self.constitution = constitution or HueyConstitution()
        self.rules = rules or RuleEngine()
        self.audit_log = audit_log or AuditLog()
        self._register_default_rules()

    def _register_default_rules(self) -> None:
        if self.rules.evaluate({}):
            return
        self.rules.register(
            Rule(
                "risk-threshold",
                "Block actions whose declared risk exceeds 0.8.",
                lambda payload: float(payload.get("risk", 0.0)) <= 0.8,
            )
        )
        self.rules.register(
            Rule(
                "remote-control",
                "Require explicit opt-in for remote control actions.",
                lambda payload: not payload.get("remote_control") or bool(payload.get("allowed")),
            )
        )

    def authorize(self, action: str, payload: dict[str, object]) -> dict[str, object]:
        rule_results = self.rules.evaluate(payload)
        violations = [result for result in rule_results if not result["passed"]]
        approved = not violations
        rationale = "approved" if approved else "blocked by governance rules"
        entry = self.audit_log.record(
            action,
            approved=approved,
            rationale=rationale,
            metadata={"violations": violations, "payload": dict(payload)},
        )
        return {
            "approved": approved,
            "rationale": rationale,
            "violations": violations,
            "principles": self.constitution.summary(),
            "audit_entry": {
                "action": entry.action,
                "approved": entry.approved,
                "timestamp": entry.timestamp,
            },
        }


__all__ = ["PolicyEnforcer"]
