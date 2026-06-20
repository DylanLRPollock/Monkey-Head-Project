"""Base class for the speculative Spark/Volt/Zap/Watt agent family."""

from __future__ import annotations

from dataclasses import dataclass, field

from huey.ai.brain import HueyBrain
from huey.decision.binary import decide_yes_no
from huey.decision.context import DecisionContext


@dataclass(slots=True)
class AgentResponse:
    agent: str
    approved: bool
    confidence: float
    summary: str
    metadata: dict[str, object] = field(default_factory=dict)


class BaseAgent:
    """Provide a consistent interface for the four named agents."""

    name = "BaseAgent"
    role = "general"
    approval_bias = 0.0

    def __init__(self, brain: HueyBrain | None = None) -> None:
        self.brain = brain or HueyBrain()

    def build_context(
        self, task: str, *, metadata: dict[str, object] | None = None
    ) -> DecisionContext:
        meta = dict(metadata or {})
        signals = {
            "urgency": float(meta.get("urgency", 0.5)),
            "risk_inverse": 1.0 - float(meta.get("risk", 0.25)),
            "fit": float(meta.get("fit", 0.65)),
        }
        constraints = [str(item) for item in meta.get("constraints", ())]
        return DecisionContext(goal=task, signals=signals, constraints=constraints, metadata=meta)

    def respond(
        self, task: str, *, metadata: dict[str, object] | None = None
    ) -> AgentResponse:
        context = self.build_context(task, metadata=metadata)
        decision = decide_yes_no(context, bias=self.approval_bias)
        inference = self.brain.think(
            f"{self.name} ({self.role}) is evaluating: {task}",
            context={"goal": task, "metadata": dict(metadata or {})},
        )
        summary = f"{decision.rationale}; inference={inference['summary']}"
        return AgentResponse(
            agent=self.name,
            approved=decision.approved,
            confidence=decision.score,
            summary=summary,
            metadata={
                "role": self.role,
                "context": context.metadata,
                "inference": inference,
            },
        )


__all__ = ["AgentResponse", "BaseAgent"]
