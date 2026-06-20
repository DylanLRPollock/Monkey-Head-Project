"""Rule engine used to evaluate proposed actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

RulePredicate = Callable[[dict[str, object]], bool]


@dataclass(slots=True)
class Rule:
    name: str
    description: str
    predicate: RulePredicate


class RuleEngine:
    """Evaluate a payload against registered boolean rules."""

    def __init__(self) -> None:
        self._rules: list[Rule] = []

    def register(self, rule: Rule) -> None:
        self._rules.append(rule)

    def evaluate(self, payload: dict[str, object]) -> list[dict[str, object]]:
        results: list[dict[str, object]] = []
        for rule in self._rules:
            passed = bool(rule.predicate(payload))
            results.append(
                {
                    "name": rule.name,
                    "description": rule.description,
                    "passed": passed,
                }
            )
        return results


__all__ = ["Rule", "RuleEngine"]
