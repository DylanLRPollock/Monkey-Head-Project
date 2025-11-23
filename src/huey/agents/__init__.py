# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Package initializer for huey/agents

"""Agent implementations used by HueyOS."""

from .presidential import (
    ActionProposal,
    AgentDecision,
    ConsensusDecision,
    LLMProvider,
    PresidentialCouncil,
    SparkAgent,
    ZapAgent,
)

__all__ = [
    "ActionProposal",
    "AgentDecision",
    "ConsensusDecision",
    "LLMProvider",
    "PresidentialCouncil",
    "SparkAgent",
    "ZapAgent",
]
