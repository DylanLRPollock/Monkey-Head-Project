"""Lightweight shim replicating :mod:`monkey_head.main` interfaces.

The historical implementation lived under ``huey/memory/PY/main.py`` and
pulled in numerous heavy runtime dependencies.  Tests and downstream
consumers primarily rely on the public functions and objects exported by
that module rather than its side effects, so this shim provides a
self-contained version that reuses the same signatures while remaining
importable in minimal environments.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, Tuple

try:
    from monkey_head.pytorch_tools import device_summary
except ModuleNotFoundError:  # pragma: no cover - source checkout namespace
    try:
        from huey.pytorch_tools import device_summary
    except ModuleNotFoundError:  # pragma: no cover - optional torch stack absent

        def device_summary() -> Dict[str, Any]:
            return {"available": False, "reason": "torch is not installed"}


from .pyhuey_integration import pyhuey_status as get_pyhuey_status
from .agents.agent_manager import AgentManager
from .ai.brain import HueyBrain
from .bridges.api_bridge import ApiBridge
from .bridges.cognition_bridge import CognitionBridge
from .bridges.hardware_bridge import HardwareBridge
from .config import RuntimeConfig, build_runtime_config
from .gencore.kernel import GenCoreKernel
from .governance.policy import PolicyEnforcer
from .logger import configure_logging
from .settings import RuntimeSettings
from .storage.honeycomb import HoneycombStore
from .ui.interface import InterfaceController
from .version import VERSION, version_payload


@dataclass
class _Route:
    path: str
    methods: Tuple[str, ...]
    handler: Callable[..., Any]


@dataclass
class _StubApp:
    """Tiny stand-in for Flask's :class:`~flask.Flask` application.

    The stub records routes registered via :meth:`route` and offers a
    simple :meth:`run` method whose behaviour can be monkeypatched by
    tests.  This keeps the public surface compatible without requiring
    the real Flask dependency.
    """

    routes: Dict[Tuple[str, Tuple[str, ...]], _Route] = field(default_factory=dict)

    def route(
        self, path: str, *, methods: Iterable[str] | None = None
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        allowed = tuple(methods) if methods is not None else tuple()

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.routes[(path, allowed)] = _Route(path, allowed, func)
            return func

        return decorator

    def run(self, host: str, port: int) -> Dict[str, Any]:
        # Mirror Flask's return value shape loosely; tests typically
        # monkeypatch this method, so the body is intentionally simple.
        return {"host": host, "port": port}


@dataclass
class ApplicationContext:
    settings: RuntimeSettings
    config: RuntimeConfig
    kernel: GenCoreKernel
    brain_bridge: CognitionBridge
    agents: AgentManager
    governance: PolicyEnforcer
    storage: HoneycombStore
    interface: InterfaceController
    hardware: HardwareBridge
    api_bridge: ApiBridge

    def snapshot(self) -> dict[str, Any]:
        kernel_snapshot = self.kernel.snapshot()
        return {
            "settings": self.settings.to_dict(),
            "config": self.config.to_dict(),
            "kernel": kernel_snapshot,
            "agents": self.agents.list_agents(),
            "governance": self.governance.authorize(
                "runtime.snapshot",
                {"risk": 0.0, "remote_control": False, "allowed": True},
            ),
            "hardware": self.hardware.snapshot(),
            "api_routes": self.api_bridge.describe(),
        }


def jsonify(**payload: Any) -> Dict[str, Any]:
    """Return a JSON-serialisable payload.

    The real Flask helper builds a response object; for testing purposes,
    a plain dictionary is sufficient and easier to inspect.
    """

    return payload


app = _StubApp()


@app.route("/health", methods=["GET"])
def health_check() -> tuple[Dict[str, str], int]:
    return {"status": "healthy"}, 200


@app.route("/ready", methods=["GET"])
def readiness_check() -> tuple[Dict[str, str], int]:
    return {"status": "ready"}, 200


@app.route("/version", methods=["GET"])
def version_info(version: str = VERSION) -> tuple[Dict[str, str], int]:
    payload = version_payload()
    payload["version"] = version
    return payload, 200


@app.route("/pytorch/info", methods=["GET"])
def pytorch_info() -> tuple[Dict[str, Any], int]:
    return device_summary(), 200


@app.route("/pyhuey/status", methods=["GET"])
def pyhuey_status() -> tuple[Dict[str, Any], int]:
    return get_pyhuey_status(), 200


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the Monkey Head server."""

    parser = argparse.ArgumentParser(description="Start Monkey Head server")
    parser.add_argument(
        "--skip-setup",
        action="store_true",
        help="Skip environment setup steps",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host interface to bind",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=4488,
        help="Port to listen on",
    )
    return parser.parse_args(args)


def run_setup() -> None:
    """Placeholder for the historical setup routine."""

    global RUNTIME_CONTEXT
    RUNTIME_CONTEXT = build_application_context()
    return None


def build_application_context(
    settings: RuntimeSettings | None = None,
) -> ApplicationContext:
    """Bootstrap the speculative subsystem tree inside the existing package."""

    resolved_settings = settings or RuntimeSettings.from_env()
    configure_logging(resolved_settings)
    runtime_config = build_runtime_config(settings=resolved_settings)
    kernel = GenCoreKernel(resolved_settings)
    kernel.bootstrap()
    brain = HueyBrain()
    agents = AgentManager(brain)
    cognition = CognitionBridge(brain, agents)
    governance = PolicyEnforcer()
    storage = HoneycombStore()
    interface = InterfaceController()
    hardware = HardwareBridge(kernel)
    api_bridge = ApiBridge(kernel, agents=agents, governance=governance)
    storage.put(
        "runtime/bootstrap",
        {
            "settings": resolved_settings.to_dict(),
            "boot": kernel.health_report(),
            "agents": agents.list_agents(),
        },
        labels=["runtime", "bootstrap"],
    )
    kernel.create_process(
        "huey-main",
        metadata={"environment": resolved_settings.environment},
    )
    return ApplicationContext(
        settings=resolved_settings,
        config=runtime_config,
        kernel=kernel,
        brain_bridge=cognition,
        agents=agents,
        governance=governance,
        storage=storage,
        interface=interface,
        hardware=hardware,
        api_bridge=api_bridge,
    )


def main() -> None:
    """Run setup tasks and start the minimal health service."""

    args = parse_args()
    if not args.skip_setup:
        run_setup()
    app.run(host=args.host, port=args.port)


RUNTIME_CONTEXT: ApplicationContext | None = None

__all__ = [
    "ApplicationContext",
    "app",
    "build_application_context",
    "health_check",
    "readiness_check",
    "version_info",
    "pytorch_info",
    "pyhuey_status",
    "parse_args",
    "run_setup",
    "main",
    "jsonify",
    "RUNTIME_CONTEXT",
]
