"""Deterministic tests for base agents, the message bus, and consensus."""

from __future__ import annotations

from huey.agents.agent_communication import AgentMessageBus
from huey.agents.agent_manager import AgentManager
from huey.agents.base_agent import AgentResponse, BaseAgent
from huey.decision.context import DecisionContext


class FakeBrain:
    def think(self, prompt, *, context=None):
        return {"summary": f"processed: {prompt}", "context": context or {}}


class FixedAgent:
    def __init__(self, name, approved, confidence):
        self.name = name
        self.approved = approved
        self.confidence = confidence

    def respond(self, task, *, metadata=None):
        return AgentResponse(
            agent=self.name,
            approved=self.approved,
            confidence=self.confidence,
            summary=task,
            metadata=dict(metadata or {}),
        )


def test_base_agent_builds_context_and_returns_brain_summary():
    agent = BaseAgent(FakeBrain())
    context = agent.build_context(
        "review plan",
        metadata={"urgency": 0.8, "risk": 0.4, "fit": 0.9, "constraints": ["offline", 3]},
    )
    assert context == DecisionContext(
        goal="review plan",
        signals={"urgency": 0.8, "risk_inverse": 0.6, "fit": 0.9},
        constraints=["offline", "3"],
        metadata={"urgency": 0.8, "risk": 0.4, "fit": 0.9, "constraints": ["offline", 3]},
    )

    response = agent.respond("review plan")
    assert response.agent == "BaseAgent"
    assert response.metadata["role"] == "general"
    assert "processed: BaseAgent (general) is evaluating: review plan" in response.summary
    assert response.metadata["context"] == {}


def test_message_bus_copies_metadata_and_filters_inbox():
    bus = AgentMessageBus()
    metadata = {"approved": True}
    first = bus.publish("manager", "spark", "dispatch", "task", metadata=metadata)
    bus.publish("manager", "volt", "dispatch", "task 2")
    metadata["approved"] = False
    assert first.metadata == {"approved": True}
    assert [message.target for message in bus.inbox("spark")] == ["spark"]
    history = bus.history()
    assert len(history) == 2
    history[0]["metadata"]["approved"] = False
    assert bus.history()[0]["metadata"] == {"approved": True}


def test_agent_manager_dispatch_serializes_responses_and_publishes_messages():
    manager = AgentManager(FakeBrain())
    manager.register_agent(FixedAgent("custom", True, 0.75))
    result = manager.dispatch("build a test", metadata={"source": "suite"})
    assert manager.list_agents() == ["Spark-4", "Volt-4", "Watt-4", "Zap-4", "custom"]
    assert result["custom"] == {
        "agent": "custom",
        "approved": True,
        "confidence": 0.75,
        "summary": "build a test",
        "metadata": {"source": "suite"},
    }
    inbox = manager.message_bus.inbox("custom")
    assert len(inbox) == 1
    assert inbox[0].metadata == {"approved": True}


def test_agent_manager_consensus_threshold_and_empty_agent_set():
    manager = AgentManager(FakeBrain())
    manager._agents = {
        "one": FixedAgent("one", True, 0.9),
        "two": FixedAgent("two", True, 0.8),
        "three": FixedAgent("three", False, 0.3),
    }
    consensus = manager.consensus("choose")
    assert consensus["approved"] is True
    assert consensus["average_confidence"] == 0.666667
    assert len(consensus["responses"]) == 3

    manager._agents.clear()
    empty = manager.consensus("no agents")
    assert empty["approved"] is False
    assert empty["average_confidence"] == 0.0
    assert empty["responses"] == {}
