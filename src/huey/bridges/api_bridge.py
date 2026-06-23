"""Bridge runtime state into an API surface."""

from __future__ import annotations

from huey.agents.agent_manager import AgentManager
from huey.gencore.kernel import GenCoreKernel
from huey.governance.policy import PolicyEnforcer
from huey.network.api import ApiSurface


class ApiBridge:
    """Expose kernel, agent, and governance summaries as API routes."""

    def __init__(
        self,
        kernel: GenCoreKernel,
        *,
        agents: AgentManager | None = None,
        governance: PolicyEnforcer | None = None,
    ) -> None:
        self.kernel = kernel
        self.agents = agents or AgentManager()
        self.governance = governance or PolicyEnforcer()
        self.surface = ApiSurface()
        self._register_routes()

    def _register_routes(self) -> None:
        self.surface.register("/healthz", "GET", self.kernel.health_report)
        self.surface.register("/kernel", "GET", self.kernel.snapshot)
        self.surface.register(
            "/agents",
            "GET",
            lambda: {"agents": self.agents.list_agents()},
        )
        self.surface.register(
            "/governance",
            "GET",
            lambda: self.governance.authorize(
                "status",
                {"risk": 0.0, "remote_control": False, "allowed": True},
            ),
        )

    def describe(self) -> list[dict[str, object]]:
        return self.surface.describe()


__all__ = ["ApiBridge"]
