"""Bicameral presidential agent architecture (Spark and Zap)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid5, NAMESPACE_URL

from monkey_head.honeycomb_storage import HoneycombStorage, ConversationEntry
from monkey_head.llm import PyGPTLLMClient, StructuredDecision


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class AgentMetadata:
    uuid: str
    name: str
    capabilities: List[str]
    model: str
    agent_provider: str
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ActionProposal:
    action_id: str
    summary: str
    details: str
    risk_level: str = "medium"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentDecision:
    action_id: str
    agent_name: str
    approved: bool
    rationale: str
    confidence: float
    structured: StructuredDecision
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConsensusResult:
    action_id: str
    outcome: str
    decisions: List[AgentDecision]
    rationale: str
    human_override: Optional[bool] = None


def _load_agent_template() -> Dict[str, Any]:
    template_path = (
        Path(__file__).resolve().parents[2]
        / "huey"
        / "memory"
        / "JSON"
        / "agent_openai.json"
    )
    with template_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


AGENT_TEMPLATE = _load_agent_template()


def _metadata_from_template(name: str, capabilities: Iterable[str]) -> AgentMetadata:
    template = dict(AGENT_TEMPLATE)
    uuid = str(uuid5(NAMESPACE_URL, f"monkey-head::{name.lower()}"))
    model = template.get("model", "gpt-4o")
    provider = template.get("agent_provider", "openai")
    extra = {
        "temperature": template.get("temperature", 1.0),
        "tools": template.get("tools", {}),
        "template_version": template.get("__meta__", {}).get("version"),
    }
    return AgentMetadata(
        uuid=uuid,
        name=name,
        capabilities=list(capabilities),
        model=model,
        agent_provider=provider,
        extra=extra,
    )


class PresidentialAgent:
    """Base class encapsulating decision, memory, and communication logic."""

    def __init__(
        self,
        metadata: AgentMetadata,
        memory: HoneycombStorage,
        llm_client: PyGPTLLMClient,
        persona: str,
    ) -> None:
        self.metadata = metadata
        self.memory = memory
        self.llm_client = llm_client
        self.persona = persona

    # ------------------------------------------------------------------
    def _format_history(self, entries: List[ConversationEntry]) -> List[Dict[str, Any]]:
        history_payload: List[Dict[str, Any]] = []
        for entry in entries:
            history_payload.append(
                {
                    "agent": entry.agent,
                    "role": entry.role,
                    "content": entry.content,
                    "timestamp": entry.created_at.isoformat(),
                    "metadata": entry.metadata,
                }
            )
        return history_payload

    # ------------------------------------------------------------------
    def _compose_persona(self, action: ActionProposal) -> str:
        capability_summary = ", ".join(self.metadata.capabilities)
        return (
            f"{self.metadata.name} persona: {self.persona}. "
            f"Capabilities: {capability_summary}. "
            f"Action summary: {action.summary}. Risk: {action.risk_level}."
        )

    # ------------------------------------------------------------------
    def evaluate(self, action: ActionProposal) -> AgentDecision:
        LOGGER.info(
            "Agent %s evaluating action %s",
            self.metadata.name,
            action.action_id,
        )
        history_entries = self.memory.get_conversation(action.action_id)
        formatted_history = self._format_history(history_entries)
        persona_prompt = self._compose_persona(action)
        action_payload = {
            "action_id": action.action_id,
            "summary": action.summary,
            "details": action.details,
            "risk_level": action.risk_level,
            "metadata": action.metadata,
        }

        prompt_metadata = {
            "persona": persona_prompt,
            "capabilities": self.metadata.capabilities,
        }
        self.memory.append_conversation(
            action.action_id,
            self.metadata.name,
            "prompt",
            persona_prompt,
            metadata=prompt_metadata,
        )

        structured = self.llm_client.generate_decision(
            persona=persona_prompt,
            action=action_payload,
            history=formatted_history,
        )

        approved = structured.decision in {"approve", "approved", "yes"}
        rationale = structured.rationale
        metadata = {
            "confidence": structured.confidence,
            "analysis": structured.analysis,
            "provider": self.metadata.agent_provider,
        }

        self.memory.append_conversation(
            action.action_id,
            self.metadata.name,
            "analysis",
            structured.analysis,
            metadata=metadata,
        )

        LOGGER.info(
            "Agent %s decision on %s: %s (confidence %.2f)",
            self.metadata.name,
            action.action_id,
            "approve" if approved else "reject",
            structured.confidence,
        )

        return AgentDecision(
            action_id=action.action_id,
            agent_name=self.metadata.name,
            approved=approved,
            rationale=rationale,
            confidence=structured.confidence,
            structured=structured,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    def communicate(
        self,
        action_id: str,
        recipient: "PresidentialAgent",
        message: str,
    ) -> None:
        self.memory.append_conversation(
            action_id,
            self.metadata.name,
            "communication",
            message,
            metadata={"recipient": recipient.metadata.name},
        )
        LOGGER.debug(
            "Agent %s sent message to %s for action %s",
            self.metadata.name,
            recipient.metadata.name,
            action_id,
        )


class SparkAgent(PresidentialAgent):
    def __init__(self, memory: HoneycombStorage, llm_client: PyGPTLLMClient) -> None:
        metadata = _metadata_from_template(
            "Spark",
            [
                "Strategic foresight",
                "Policy alignment",
                "Long-term risk mitigation",
            ],
        )
        persona = (
            "Visionary strategist focused on systems thinking, policy cohesion, "
            "and ethical governance across long horizons"
        )
        super().__init__(metadata, memory, llm_client, persona)


class ZapAgent(PresidentialAgent):
    def __init__(self, memory: HoneycombStorage, llm_client: PyGPTLLMClient) -> None:
        metadata = _metadata_from_template(
            "Zap",
            [
                "Operational execution",
                "Resource optimisation",
                "Rapid contingency response",
            ],
        )
        persona = (
            "Pragmatic tactician specialising in execution detail, resource "
            "balancing, and adaptive field operations"
        )
        super().__init__(metadata, memory, llm_client, persona)


class PresidentialCouncil:
    """Consensus mechanism requiring Spark and Zap alignment."""

    def __init__(self, spark: SparkAgent, zap: ZapAgent, memory: HoneycombStorage) -> None:
        self.spark = spark
        self.zap = zap
        self.memory = memory

    # ------------------------------------------------------------------
    def deliberate(
        self,
        action: ActionProposal,
        *,
        human_override: Optional[bool] = None,
    ) -> ConsensusResult:
        decisions = [self.spark.evaluate(action), self.zap.evaluate(action)]
        approvals = {decision.approved for decision in decisions}

        if len(approvals) == 1:
            approved = approvals.pop()
            outcome = "approved" if approved else "rejected"
            rationale = "Spark and Zap reached unanimous consensus."
            override = None
        else:
            if human_override is None:
                outcome = "requires_human_override"
                rationale = (
                    "Spark and Zap are split. Decision escalated for human override "
                    "per bicameral fail-safe."
                )
                override = None
            else:
                outcome = "approved" if human_override else "rejected"
                rationale = (
                    "Human override applied to resolve Spark/Zap disagreement."
                )
                override = human_override

        LOGGER.info(
            "Presidential council outcome for %s: %s",
            action.action_id,
            outcome,
        )

        self.memory.append_conversation(
            action.action_id,
            "PresidentialCouncil",
            "consensus",
            rationale,
            metadata={
                "outcome": outcome,
                "decisions": [
                    {
                        "agent": decision.agent_name,
                        "approved": decision.approved,
                        "confidence": decision.confidence,
                    }
                    for decision in decisions
                ],
                "human_override": override,
            },
        )

        return ConsensusResult(
            action_id=action.action_id,
            outcome=outcome,
            decisions=decisions,
            rationale=rationale,
            human_override=override,
        )

