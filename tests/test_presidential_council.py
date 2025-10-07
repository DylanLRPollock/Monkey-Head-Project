from monkey_head.agents import (
    ActionProposal,
    PresidentialCouncil,
    SparkAgent,
    ZapAgent,
)
from monkey_head.honeycomb_storage import HoneycombStorage
from monkey_head.llm import PyGPTLLMClient


def _make_executor(spark_response, zap_response):
    def executor(*, provider, model, persona, action, history, provider_metadata):
        if persona.startswith("Spark persona"):
            return spark_response
        if persona.startswith("Zap persona"):
            return zap_response
        raise RuntimeError("Unknown persona request")

    return executor


def _build_agents(tmp_path, executor):
    storage = HoneycombStorage(base_dir=tmp_path)
    spark_client = PyGPTLLMClient(model="gpt-4o", executor=executor)
    zap_client = PyGPTLLMClient(model="gpt-4o", executor=executor)
    spark = SparkAgent(storage, spark_client)
    zap = ZapAgent(storage, zap_client)
    council = PresidentialCouncil(spark, zap, storage)
    return storage, council


def test_consensus_approval(tmp_path):
    executor = _make_executor(
        {
            "decision": "approve",
            "rationale": "Strategic objectives satisfied",
            "confidence": 0.85,
            "analysis": "Spark approves",
        },
        {
            "decision": "approve",
            "rationale": "Operational checks complete",
            "confidence": 0.8,
            "analysis": "Zap approves",
        },
    )
    storage, council = _build_agents(tmp_path, executor)
    action = ActionProposal(
        action_id="deploy-1",
        summary="Deploy update",
        details="Roll out patch",
        risk_level="low",
    )
    result = council.deliberate(action)

    assert result.outcome == "approved"
    assert all(decision.approved for decision in result.decisions)

    history = storage.get_conversation("deploy-1")
    assert any(entry.role == "consensus" for entry in history)


def test_split_requires_human_override(tmp_path):
    executor = _make_executor(
        {
            "decision": "approve",
            "rationale": "Long-term alignment",
            "confidence": 0.7,
            "analysis": "Spark approve",
        },
        {
            "decision": "reject",
            "rationale": "Operational risk",
            "confidence": 0.6,
            "analysis": "Zap reject",
        },
    )
    storage, council = _build_agents(tmp_path, executor)
    action = ActionProposal(
        action_id="deploy-2",
        summary="Deploy risky change",
        details="High risk patch",
        risk_level="high",
    )

    result = council.deliberate(action)

    assert result.outcome == "requires_human_override"
    assert result.human_override is None

    override_result = council.deliberate(action, human_override=False)
    assert override_result.outcome == "rejected"
    assert override_result.human_override is False
