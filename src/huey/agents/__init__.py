# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Package initializer for huey/agents

"""Agent implementations used by HueyOS."""

from .agent_communication import AgentMessage, AgentMessageBus
from .agent_manager import AgentManager
from .base_agent import AgentResponse, BaseAgent
from .presidential import (
    ActionProposal,
    AgentDecision,
    ConsensusDecision,
    LLMProvider,
    PresidentialCouncil,
    SparkAgent,
    ZapAgent,
)
from .spark4 import Spark4Agent
from .volt4 import Volt4Agent
from .watt4 import Watt4Agent
from .zap4 import Zap4Agent

__all__ = [
    "ActionProposal",
    "AgentManager",
    "AgentDecision",
    "AgentMessage",
    "AgentMessageBus",
    "AgentResponse",
    "BaseAgent",
    "ConsensusDecision",
    "LLMProvider",
    "PresidentialCouncil",
    "SparkAgent",
    "Spark4Agent",
    "Volt4Agent",
    "Watt4Agent",
    "ZapAgent",
    "Zap4Agent",
]
