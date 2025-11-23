# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Presidential module (huey/agents)

"""Bicameral presidential agent structure for HueyOS."""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from huey.honeycomb.storage import HoneycombStorage

from .llm import LLMAdapter, LLMProvider
from .memory import AgentMemory, MemoryEntry

LOGGER = logging.getLogger(__name__)

_TEMPLATE_CACHE: Dict[str, Any] | None = None
_TEMPLATE_PATH = (
    Path(__file__).resolve().parents[2]
    / "huey"
    / "memory"
    / "JSON"
    / "agent_openai.json"
)


@dataclass(frozen=True)
class AgentMetadata:
    """Metadata describing an agent, derived from the OpenAI template."""

    uuid: str
    name: str
    capabilities: List[str]
    provider: LLMProvider
    model: str
    filename: str

    @property
    def agent_id(self) -> str:
        return self.name.lower().replace(" ", "-")

    @classmethod
    def from_template(
        cls,
        *,
        name: str,
        provider: LLMProvider,
        model: str,
        capabilities: Iterable[str],
        filename: str,
    ) -> "AgentMetadata":
        template = _load_template()
        base_uuid = uuid.UUID(template.get("uuid", uuid.uuid4().hex))
        derived_uuid = uuid.uuid5(base_uuid, name)
        return cls(
            uuid=str(derived_uuid),
            name=name,
            capabilities=list(capabilities),
            provider=provider,
            model=model,
            filename=filename,
        )


@dataclass(frozen=True)
class ActionProposal:
    """A proposed action that requires executive approval."""

    action_id: str
    description: str
    context: Optional[str] = None
    tags: Sequence[str] = field(default_factory=tuple)
    requested_by: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_prompt(self) -> str:
        """Render the proposal as a prompt for LLM analysis."""

        prompt = {
            "action_id": self.action_id,
            "description": self.description,
            "context": self.context,
            "tags": list(self.tags),
            "requested_by": self.requested_by,
            "metadata": self.metadata,
        }
        return json.dumps(prompt, indent=2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "description": self.description,
            "context": self.context,
            "tags": list(self.tags),
            "requested_by": self.requested_by,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class AgentDecision:
    """Decision rendered by an agent."""

    agent: str
    approved: bool
    confidence: float
    rationale: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConsensusDecision:
    """Outcome of the presidential council."""

    proposal: ActionProposal
    approved: bool
    rationale: str
    votes: Dict[str, AgentDecision]
    fallback_reason: Optional[str]
    human_override: Optional[bool]
    timestamp: float


class PresidentialAgent:
    """Base class shared by Spark and Zap."""

    def __init__(
        self,
        metadata: AgentMetadata,
        *,
        memory: AgentMemory,
        llm: LLMAdapter,
        threshold: float,
    ) -> None:
        self.metadata = metadata
        self.memory = memory
        self.llm = llm
        self.threshold = threshold
        self.logger = logging.getLogger(f"{__name__}.{self.metadata.agent_id}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def deliberate(self, proposal: ActionProposal) -> AgentDecision:
        """Evaluate ``proposal`` returning a structured decision."""

        history = self.memory.last_decisions(limit=3)
        base_score = self._score_proposal(proposal, history)
        base_score = min(max(base_score, 0.0), 1.0)
        llm_feedback = self._solicit_llm_feedback(proposal, base_score, history)
        adjusted_score = self._combine_scores(base_score, llm_feedback)
        approved = adjusted_score >= self.threshold
        rationale = self._compose_rationale(
            proposal,
            base_score=base_score,
            adjusted_score=adjusted_score,
            approved=approved,
            llm_feedback=llm_feedback,
        )
        timestamp = proposal.metadata.get("timestamp") or time.time()
        decision = AgentDecision(
            agent=self.metadata.name,
            approved=approved,
            confidence=adjusted_score,
            rationale=rationale,
            timestamp=timestamp,
            metadata={
                "base_score": base_score,
                "threshold": self.threshold,
                "llm_feedback": llm_feedback,
            },
        )
        self._persist_decision(proposal, decision)
        return decision

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _score_proposal(
        self, proposal: ActionProposal, history: Sequence[MemoryEntry]
    ) -> float:
        """Return a heuristic score between 0 and 1 for ``proposal``."""

        score = 0.5
        tags = {tag.lower() for tag in proposal.tags}
        if "emergency" in tags:
            score += 0.1
        if "maintenance" in tags:
            score += 0.05
        risk = float(proposal.metadata.get("risk", 0.3))
        score -= risk * 0.2
        if history:
            score += 0.02 * len(history)
        return score

    def _solicit_llm_feedback(
        self,
        proposal: ActionProposal,
        base_score: float,
        history: Sequence[MemoryEntry],
    ) -> Optional[str]:
        """Ask the configured LLM for a short opinion on the proposal."""

        try:
            prompt = (
                "You are {name}, reviewing an action for HueyOS. Current score: {score:.2f}. "
                "Recent decisions: {history}. Proposal JSON: {payload}."
            ).format(
                name=self.metadata.name,
                score=base_score,
                history=[entry.payload.get("decision") for entry in history],
                payload=proposal.to_prompt(),
            )
            response = self.llm.generate(prompt)
            return response
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.warning("LLM feedback failed: %s", exc)
            return None

    def _combine_scores(self, base_score: float, llm_feedback: Optional[str]) -> float:
        score = base_score
        if llm_feedback:
            text = llm_feedback.lower()
            modifier = 0.0
            if any(token in text for token in ("approve", "proceed", "green")):
                modifier += 0.15
            if any(token in text for token in ("reject", "halt", "stop")):
                modifier -= 0.2
            if "risk" in text:
                modifier -= 0.1
            score = min(max((base_score + (base_score + modifier)) / 2, 0.0), 1.0)
        return score

    def _compose_rationale(
        self,
        proposal: ActionProposal,
        *,
        base_score: float,
        adjusted_score: float,
        approved: bool,
        llm_feedback: Optional[str],
    ) -> str:
        fragments = [
            f"Base score {base_score:.2f} with threshold {self.threshold:.2f}.",
            f"Adjusted score {adjusted_score:.2f} -> {'approve' if approved else 'reject'}.",
        ]
        if llm_feedback:
            fragments.append(f"LLM insight: {llm_feedback}")
        if proposal.metadata:
            fragments.append(f"Metadata considered: {json.dumps(proposal.metadata)}")
        return " ".join(fragments)

    def _persist_decision(
        self, proposal: ActionProposal, decision: AgentDecision
    ) -> None:
        payload = {
            "proposal": proposal.to_dict(),
            "decision": {
                "approved": decision.approved,
                "confidence": decision.confidence,
                "rationale": decision.rationale,
            },
            "meta": decision.metadata,
        }
        self.memory.remember("decision", payload)
        self.memory.log_conversation(
            proposal.action_id,
            role=self.metadata.name,
            content=decision.rationale,
            metadata={
                "approved": decision.approved,
                "confidence": decision.confidence,
                "base_score": decision.metadata.get("base_score"),
            },
        )
        self.logger.info(
            "%s decided %s on %s (confidence %.2f)",
            self.metadata.name,
            "approve" if decision.approved else "reject",
            proposal.action_id,
            decision.confidence,
        )


class SparkAgent(PresidentialAgent):
    """Creative oriented co-president."""

    def __init__(
        self,
        storage: Optional[HoneycombStorage] = None,
        *,
        llm_settings: Optional[Dict[str, Any]] = None,
    ) -> None:
        storage = storage or HoneycombStorage()
        llm_settings = llm_settings or {}
        provider_value = llm_settings.get("provider", LLMProvider.OPENAI)
        provider = (
            provider_value
            if isinstance(provider_value, LLMProvider)
            else LLMProvider(provider_value)
        )
        model = llm_settings.get("model", "gpt-4o")
        metadata = AgentMetadata.from_template(
            name="Spark-4",
            provider=provider,
            model=model,
            capabilities=[
                "creative ideation",
                "constitutional interpretation",
                "strategic synthesis",
            ],
            filename="agent_spark",
        )
        memory = AgentMemory(storage, metadata.uuid)
        llm_adapter = LLMAdapter(provider, model=model, settings=llm_settings)
        super().__init__(metadata, memory=memory, llm=llm_adapter, threshold=0.55)

    def _score_proposal(
        self, proposal: ActionProposal, history: Sequence[MemoryEntry]
    ) -> float:
        score = super()._score_proposal(proposal, history)
        tags = {tag.lower() for tag in proposal.tags}
        if "innovation" in tags or "creative" in tags:
            score += 0.2
        if "exploratory" in tags:
            score += 0.1
        risk = float(proposal.metadata.get("risk", 0.3))
        score -= risk * 0.1
        return min(max(score, 0.0), 1.0)


class ZapAgent(PresidentialAgent):
    """Operational and safety focused co-president."""

    def __init__(
        self,
        storage: Optional[HoneycombStorage] = None,
        *,
        llm_settings: Optional[Dict[str, Any]] = None,
    ) -> None:
        storage = storage or HoneycombStorage()
        llm_settings = llm_settings or {}
        provider_value = llm_settings.get("provider", LLMProvider.OLLAMA)
        provider = (
            provider_value
            if isinstance(provider_value, LLMProvider)
            else LLMProvider(provider_value)
        )
        model = llm_settings.get("model", "mistral")
        metadata = AgentMetadata.from_template(
            name="Zap-4",
            provider=provider,
            model=model,
            capabilities=[
                "operational oversight",
                "risk mitigation",
                "sensor fusion",
            ],
            filename="agent_zap",
        )
        memory = AgentMemory(storage, metadata.uuid)
        llm_adapter = LLMAdapter(provider, model=model, settings=llm_settings)
        super().__init__(metadata, memory=memory, llm=llm_adapter, threshold=0.65)

    def _score_proposal(
        self, proposal: ActionProposal, history: Sequence[MemoryEntry]
    ) -> float:
        score = super()._score_proposal(proposal, history)
        risk = float(proposal.metadata.get("risk", 0.3))
        score -= risk * 0.3
        if proposal.metadata.get("requires_manual_override"):
            score -= 0.2
        tags = {tag.lower() for tag in proposal.tags}
        if "safety" in tags:
            score += 0.1
        return min(max(score, 0.0), 1.0)


class PresidentialCouncil:
    """Coordinates the bicameral presidential structure."""

    def __init__(
        self,
        *,
        storage: Optional[HoneycombStorage] = None,
        spark: Optional[SparkAgent] = None,
        zap: Optional[ZapAgent] = None,
    ) -> None:
        self.storage = storage or HoneycombStorage()
        self.spark = spark or SparkAgent(storage=self.storage)
        self.zap = zap or ZapAgent(storage=self.storage)

    def decide(
        self,
        proposal: ActionProposal,
        *,
        human_override: Optional[bool] = None,
    ) -> ConsensusDecision:
        """Run the consensus workflow for ``proposal``."""

        spark_decision = self.spark.deliberate(proposal)
        zap_decision = self.zap.deliberate(proposal)
        votes = {
            self.spark.metadata.name: spark_decision,
            self.zap.metadata.name: zap_decision,
        }
        approved = spark_decision.approved and zap_decision.approved
        fallback_reason: Optional[str] = None

        if spark_decision.approved != zap_decision.approved:
            if human_override is not None:
                approved = human_override
                fallback_reason = "Human override applied"
            else:
                approved = False
                fallback_reason = "Agents disagreed; defaulting to fail-safe rejection pending human review."

        rationale = self._compose_council_rationale(votes, fallback_reason)
        timestamp = max(spark_decision.timestamp, zap_decision.timestamp)
        consensus = ConsensusDecision(
            proposal=proposal,
            approved=approved,
            rationale=rationale,
            votes=votes,
            fallback_reason=fallback_reason,
            human_override=human_override,
            timestamp=timestamp,
        )
        self._log_consensus(consensus)
        return consensus

    def _compose_council_rationale(
        self, votes: Dict[str, AgentDecision], fallback: Optional[str]
    ) -> str:
        fragments = []
        for agent, decision in votes.items():
            fragments.append(
                f"{agent} -> {'approve' if decision.approved else 'reject'} (confidence {decision.confidence:.2f})"
            )
        if fallback:
            fragments.append(f"Fallback: {fallback}")
        return " | ".join(fragments)

    def _log_consensus(self, decision: ConsensusDecision) -> None:
        payload = {
            "proposal": decision.proposal.to_dict(),
            "approved": decision.approved,
            "rationale": decision.rationale,
            "votes": {
                agent: {
                    "approved": vote.approved,
                    "confidence": vote.confidence,
                    "rationale": vote.rationale,
                }
                for agent, vote in decision.votes.items()
            },
            "fallback_reason": decision.fallback_reason,
            "human_override": decision.human_override,
            "timestamp": decision.timestamp,
        }
        key = f"consensus/{decision.proposal.action_id}/{uuid.uuid4().hex}"
        self.storage.store(key, payload)
        LOGGER.info(
            "Consensus on %s -> %s", decision.proposal.action_id, decision.approved
        )


def _load_template() -> Dict[str, Any]:
    global _TEMPLATE_CACHE
    if _TEMPLATE_CACHE is not None:
        return _TEMPLATE_CACHE
    if not _TEMPLATE_PATH.exists():
        raise FileNotFoundError(
            f"Expected template at {_TEMPLATE_PATH} to derive agent metadata"
        )
    _TEMPLATE_CACHE = json.loads(_TEMPLATE_PATH.read_text(encoding="utf-8"))
    return _TEMPLATE_CACHE


__all__ = [
    "ActionProposal",
    "AgentDecision",
    "AgentMetadata",
    "ConsensusDecision",
    "LLMAdapter",
    "LLMProvider",
    "PresidentialCouncil",
    "SparkAgent",
    "ZapAgent",
]
