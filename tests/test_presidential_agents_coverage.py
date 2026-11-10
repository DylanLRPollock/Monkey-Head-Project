"""Deterministic coverage for presidential decision and consensus paths."""

from __future__ import annotations

import json
import uuid
from types import SimpleNamespace

import pytest

import huey.agents.presidential as presidential
from huey.agents.llm import LLMAdapter, LLMProvider
from huey.agents.memory import MemoryEntry
from huey.agents.presidential import (
    ActionProposal,
    AgentDecision,
    AgentMetadata,
    PresidentialAgent,
    PresidentialCouncil,
    SparkAgent,
    ZapAgent,
)


class MemoryStub:
    def __init__(self, history=()):
        self.history = list(history)
        self.remembered = []
        self.conversations = []

    def last_decisions(self, limit=5):
        return self.history[-limit:]

    def remember(self, topic, payload):
        self.remembered.append((topic, payload))

    def log_conversation(self, conversation_id, **kwargs):
        self.conversations.append((conversation_id, kwargs))


class StorageStub:
    def __init__(self):
        self.records = []

    def store(self, key, payload):
        self.records.append((key, payload))
        return SimpleNamespace(key=key, created_at=1.0, updated_at=2.0)

    def append_conversation(self, conversation_id, **kwargs):
        self.records.append((conversation_id, kwargs))
        return SimpleNamespace(key=conversation_id, created_at=1.0, updated_at=2.0)

    def query(self, prefix, limit=None):
        return []


class LLMStub:
    def __init__(self, response="approve"):
        self.response = response
        self.prompts = []

    def generate(self, prompt):
        self.prompts.append(prompt)
        return self.response


def _metadata(name="Unit Agent"):
    return AgentMetadata(
        uuid="agent-uuid",
        name=name,
        capabilities=["review"],
        provider=LLMProvider.LOCAL,
        model="test-model",
        filename="agent-test",
    )


def _agent(*, threshold=0.5, history=(), response="approve"):
    memory = MemoryStub(history)
    llm = LLMStub(response)
    agent = PresidentialAgent(_metadata(), memory=memory, llm=llm, threshold=threshold)
    return agent, memory, llm


def _proposal(**kwargs):
    defaults = {"action_id": "action-1", "description": "Run maintenance"}
    defaults.update(kwargs)
    return ActionProposal(**defaults)


def test_metadata_identity_is_stable_and_normalized(monkeypatch):
    base_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")
    monkeypatch.setattr(presidential, "_TEMPLATE_CACHE", {"uuid": str(base_uuid)})
    first = AgentMetadata.from_template(
        name="Spark-4",
        provider=LLMProvider.OPENAI,
        model="gpt-test",
        capabilities=("plan", "review"),
        filename="spark.json",
    )
    second = AgentMetadata.from_template(
        name="Spark-4",
        provider=LLMProvider.OPENAI,
        model="other-model",
        capabilities=(),
        filename="other.json",
    )
    assert first.uuid == str(uuid.uuid5(base_uuid, "Spark-4"))
    assert first.uuid == second.uuid
    assert first.agent_id == "spark-4"
    assert first.capabilities == ["plan", "review"]


def test_load_template_reads_and_caches_json(tmp_path, monkeypatch):
    path = tmp_path / "template.json"
    path.write_text('{"uuid":"12345678-1234-5678-1234-567812345678"}')
    monkeypatch.setattr(presidential, "_TEMPLATE_CACHE", None)
    monkeypatch.setattr(presidential, "_TEMPLATE_PATH", path)
    loaded = presidential._load_template()
    path.write_text("invalid after first read")
    assert loaded["uuid"] == "12345678-1234-5678-1234-567812345678"
    assert presidential._load_template() is loaded


def test_load_template_reports_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(presidential, "_TEMPLATE_CACHE", None)
    monkeypatch.setattr(presidential, "_TEMPLATE_PATH", tmp_path / "missing.json")
    with pytest.raises(FileNotFoundError, match="Expected template"):
        presidential._load_template()


def test_proposal_serializes_prompt_and_defaults():
    proposal = _proposal(context="service status", tags=("maintenance",))
    data = proposal.to_dict()
    prompt = json.loads(proposal.to_prompt())
    assert data == prompt
    assert data == {
        "action_id": "action-1",
        "description": "Run maintenance",
        "context": "service status",
        "tags": ["maintenance"],
        "requested_by": "system",
        "metadata": {},
    }


def test_base_scoring_applies_tags_risk_and_history():
    prior = [MemoryEntry("k", "decision", {}, 1, 1)] * 3
    agent, _, _ = _agent(history=prior)
    assert agent._score_proposal(
        _proposal(tags=("EMERGENCY", "maintenance"), metadata={"risk": 0.5}),
        prior,
    ) == pytest.approx(0.61)
    assert agent._score_proposal(_proposal(metadata={"risk": -100}), []) == 20.5
    assert agent._score_proposal(_proposal(metadata={"risk": 100}), []) == -19.5


@pytest.mark.parametrize(
    ("feedback", "expected"),
    [
        (None, 0.6),
        ("proceed safely", 0.675),
        ("halt now", 0.5),
        ("approve but risk remains", 0.625),
        ("neutral", 0.6),
    ],
)
def test_feedback_score_modifiers(feedback, expected):
    agent, _, _ = _agent()
    assert agent._combine_scores(0.6, feedback) == pytest.approx(expected)


def test_feedback_score_clamps_at_zero_and_one():
    agent, _, _ = _agent()
    assert agent._combine_scores(0.0, "reject halt risk") == 0.0
    assert agent._combine_scores(1.0, "approve proceed green") == 1.0


def test_rationale_includes_feedback_and_metadata_only_when_present():
    agent, _, _ = _agent(threshold=0.75)
    plain = agent._compose_rationale(
        _proposal(),
        base_score=0.6,
        adjusted_score=0.6,
        approved=False,
        llm_feedback=None,
    )
    assert "LLM insight" not in plain and "Metadata considered" not in plain
    detailed = agent._compose_rationale(
        _proposal(metadata={"risk": 0.1}),
        base_score=0.6,
        adjusted_score=0.8,
        approved=True,
        llm_feedback="approve",
    )
    assert "approve" in detailed
    assert 'Metadata considered: {"risk": 0.1}' in detailed


def test_deliberation_persists_decision_and_logs_conversation():
    agent, memory, llm = _agent(threshold=0.5)
    proposal = _proposal(metadata={"timestamp": 123.0, "risk": 0.0})
    decision = agent.deliberate(proposal)
    assert decision.approved is True
    assert decision.timestamp == 123.0
    assert decision.confidence == pytest.approx(0.575)
    assert memory.remembered[0][0] == "decision"
    assert memory.remembered[0][1]["proposal"] == proposal.to_dict()
    assert memory.conversations[0][0] == "action-1"
    assert memory.conversations[0][1]["role"] == "Unit Agent"
    assert "Unit Agent" in llm.prompts[0]


def test_deliberation_uses_clock_when_proposal_timestamp_is_falsey(monkeypatch):
    agent, _, _ = _agent(response="neutral")
    monkeypatch.setattr(presidential.time, "time", lambda: 55.5)
    decision = agent.deliberate(_proposal(metadata={"timestamp": 0}))
    assert decision.timestamp == 55.5


def test_llm_feedback_exception_degrades_to_heuristic_decision():
    agent, memory, _ = _agent()
    agent.llm = SimpleNamespace(
        generate=lambda _prompt: (_ for _ in ()).throw(RuntimeError("offline"))
    )
    decision = agent.deliberate(_proposal())
    assert decision.metadata["llm_feedback"] is None
    assert decision.confidence == pytest.approx(0.44)
    assert memory.remembered


@pytest.mark.parametrize(
    ("tags", "metadata", "expected"),
    [
        (("innovation",), {}, 0.61),
        (("creative", "exploratory"), {"risk": 0.4}, 0.68),
        (("ordinary",), {"risk": 100}, 0.0),
    ],
)
def test_spark_scoring_adds_creative_and_exploratory_weight(tags, metadata, expected):
    spark = SparkAgent.__new__(SparkAgent)
    PresidentialAgent.__init__(
        spark, _metadata("Spark-4"), memory=MemoryStub(), llm=LLMStub(), threshold=0.55
    )
    assert spark._score_proposal(
        _proposal(tags=tags, metadata=metadata), []
    ) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("tags", "metadata", "expected"),
    [
        (("safety",), {}, 0.45),
        (("ordinary",), {"risk": 0.5}, 0.25),
        (("safety",), {"requires_manual_override": True, "risk": 0}, 0.4),
        (("ordinary",), {"risk": 100}, 0.0),
    ],
)
def test_zap_scoring_accounts_for_risk_override_and_safety(tags, metadata, expected):
    zap = ZapAgent.__new__(ZapAgent)
    PresidentialAgent.__init__(
        zap, _metadata("Zap-4"), memory=MemoryStub(), llm=LLMStub(), threshold=0.65
    )
    assert zap._score_proposal(
        _proposal(tags=tags, metadata=metadata), []
    ) == pytest.approx(expected)


def test_agent_constructors_accept_provider_settings_and_ollama(monkeypatch):
    monkeypatch.setattr(presidential, "_TEMPLATE_CACHE", {"uuid": str(uuid.uuid4())})
    storage = StorageStub()
    spark = SparkAgent(
        storage,
        llm_settings={"provider": "openai", "model": "gpt-test", "temperature": 0.2},
    )
    zap = ZapAgent(
        storage,
        llm_settings={
            "provider": "ollama",
            "model": "qwen-test",
            "host": "http://localhost",
        },
    )
    assert spark.metadata.provider is LLMProvider.OPENAI
    assert spark.llm.model == "gpt-test"
    assert spark.llm.settings == {
        "provider": "openai",
        "model": "gpt-test",
        "temperature": 0.2,
    }
    assert zap.metadata.provider is LLMProvider.OLLAMA
    assert zap.llm.model == "qwen-test"


def test_llm_adapter_normalizes_provider_and_uses_model_fallback():
    adapter = LLMAdapter("ollama", model="qwen-test", settings={"host": "local"})
    assert adapter.provider is LLMProvider.OLLAMA
    assert adapter.settings == {"host": "local"}
    assert (
        adapter.generate("Please review the action")
        == "qwen-test: approve with logged safeguards"
    )
    assert (
        adapter.generate("risk is present") == "qwen-test: reject until risk is reduced"
    )


class AgentStub:
    def __init__(self, name, decisions):
        self.metadata = _metadata(name)
        self._decisions = iter(decisions)

    def deliberate(self, _proposal):
        return next(self._decisions)


def _decision(agent, approved, confidence, timestamp):
    return AgentDecision(agent, approved, confidence, f"{agent} rationale", timestamp)


def test_council_unanimous_approval_records_consensus():
    storage = StorageStub()
    spark = AgentStub("Spark-4", [_decision("Spark-4", True, 0.9, 10)])
    zap = AgentStub("Zap-4", [_decision("Zap-4", True, 0.8, 12)])
    proposal = _proposal()
    outcome = PresidentialCouncil(storage=storage, spark=spark, zap=zap).decide(
        proposal
    )
    assert outcome.approved is True
    assert outcome.fallback_reason is None
    assert outcome.timestamp == 12
    assert "Spark-4 -> approve" in outcome.rationale
    assert storage.records[0][0].startswith("consensus/action-1/")
    assert storage.records[0][1]["votes"]["Zap-4"]["approved"] is True


def test_council_disagreement_fails_closed_without_override():
    council = PresidentialCouncil(
        storage=StorageStub(),
        spark=AgentStub("Spark-4", [_decision("Spark-4", True, 0.9, 2)]),
        zap=AgentStub("Zap-4", [_decision("Zap-4", False, 0.4, 3)]),
    )
    result = council.decide(_proposal())
    assert result.approved is False
    assert result.human_override is None
    assert "fail-safe rejection" in result.fallback_reason
    assert "Fallback:" in result.rationale


@pytest.mark.parametrize("override", [True, False])
def test_council_disagreement_applies_human_override(override):
    council = PresidentialCouncil(
        storage=StorageStub(),
        spark=AgentStub("Spark-4", [_decision("Spark-4", True, 0.9, 2)]),
        zap=AgentStub("Zap-4", [_decision("Zap-4", False, 0.4, 3)]),
    )
    result = council.decide(_proposal(), human_override=override)
    assert result.approved is override
    assert result.human_override is override
    assert result.fallback_reason == "Human override applied"


def test_council_unanimous_rejection_ignores_override_and_formats_rationale():
    council = PresidentialCouncil(
        storage=StorageStub(),
        spark=AgentStub("Spark-4", [_decision("Spark-4", False, 0.2, 2)]),
        zap=AgentStub("Zap-4", [_decision("Zap-4", False, 0.3, 3)]),
    )
    result = council.decide(_proposal(), human_override=True)
    assert result.approved is False
    assert result.fallback_reason is None
    assert "Spark-4 -> reject" in result.rationale


def test_council_composes_empty_vote_rationale():
    council = PresidentialCouncil(
        storage=StorageStub(),
        spark=AgentStub("Spark-4", []),
        zap=AgentStub("Zap-4", []),
    )
    assert council._compose_council_rationale({}, None) == ""
