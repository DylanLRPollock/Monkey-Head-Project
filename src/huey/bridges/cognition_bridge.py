"""Connect the central brain to the multi-agent manager."""

from __future__ import annotations

from huey.agents.agent_manager import AgentManager
from huey.ai.brain import HueyBrain


class CognitionBridge:
    """Coordinate direct reasoning and agent consensus for a task."""

    def __init__(
        self,
        brain: HueyBrain | None = None,
        agents: AgentManager | None = None,
    ) -> None:
        self.brain = brain or (agents.brain if agents is not None else HueyBrain())
        self.agents = agents or AgentManager(self.brain)

    def evaluate(
        self, task: str, *, metadata: dict[str, object] | None = None
    ) -> dict[str, object]:
        thought = self.brain.think(task, context=dict(metadata or {}))
        consensus = self.agents.consensus(task, metadata=metadata)
        return {"thought": thought, "consensus": consensus}


__all__ = ["CognitionBridge"]
