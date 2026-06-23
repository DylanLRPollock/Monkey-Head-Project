"""Agent orchestration for Spark-4, Volt-4, Zap-4, and Watt-4."""

from __future__ import annotations

from huey.ai.brain import HueyBrain

from .agent_communication import AgentMessageBus
from .base_agent import AgentResponse, BaseAgent
from .spark4 import Spark4Agent
from .volt4 import Volt4Agent
from .watt4 import Watt4Agent
from .zap4 import Zap4Agent


class AgentManager:
    """Coordinate the four primary scaffold agents."""

    def __init__(self, brain: HueyBrain | None = None) -> None:
        shared_brain = brain or HueyBrain()
        self.brain = shared_brain
        self.message_bus = AgentMessageBus()
        self._agents: dict[str, BaseAgent] = {
            agent.name: agent
            for agent in (
                Spark4Agent(shared_brain),
                Volt4Agent(shared_brain),
                Zap4Agent(shared_brain),
                Watt4Agent(shared_brain),
            )
        }

    def register_agent(self, agent: BaseAgent) -> None:
        self._agents[agent.name] = agent

    def list_agents(self) -> list[str]:
        return sorted(self._agents)

    def dispatch(
        self, task: str, *, metadata: dict[str, object] | None = None
    ) -> dict[str, dict[str, object]]:
        responses: dict[str, dict[str, object]] = {}
        for agent in self._agents.values():
            response = agent.respond(task, metadata=metadata)
            responses[agent.name] = _serialize_response(response)
            self.message_bus.publish(
                source="manager",
                target=agent.name,
                topic="dispatch",
                content=task,
                metadata={"approved": response.approved},
            )
        return responses

    def consensus(
        self, task: str, *, metadata: dict[str, object] | None = None
    ) -> dict[str, object]:
        responses = self.dispatch(task, metadata=metadata)
        approvals = [payload for payload in responses.values() if payload["approved"]]
        approved = len(approvals) >= max(1, len(responses) // 2 + len(responses) % 2)
        average_confidence = sum(
            float(payload["confidence"]) for payload in responses.values()
        ) / max(len(responses), 1)
        return {
            "approved": approved,
            "average_confidence": round(average_confidence, 6),
            "responses": responses,
        }


def _serialize_response(response: AgentResponse) -> dict[str, object]:
    return {
        "agent": response.agent,
        "approved": response.approved,
        "confidence": response.confidence,
        "summary": response.summary,
        "metadata": dict(response.metadata),
    }


__all__ = ["AgentManager"]
