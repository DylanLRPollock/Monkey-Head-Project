# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Config compatibility wrapper (src)

"""Configuration helpers for HueyOS runtime assembly."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .constants import DEFAULT_AGENT_NAMES, DEFAULT_POLICY
from .memory.PY.config import load_config as _legacy_load_config
from .settings import RuntimeSettings


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    """Normalized runtime configuration consumed by the new subsystem tree."""

    settings: RuntimeSettings
    features: dict[str, bool] = field(default_factory=dict)
    agents: tuple[str, ...] = DEFAULT_AGENT_NAMES
    governance_policy: str = DEFAULT_POLICY
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "settings": self.settings.to_dict(),
            "features": dict(self.features),
            "agents": list(self.agents),
            "governance_policy": self.governance_policy,
            "metadata": dict(self.metadata),
        }


def load_config(path: str) -> dict[str, Any]:
    """Preserve the legacy YAML loader used elsewhere in the repository."""

    return _legacy_load_config(path)


def merge_feature_flags(
    base: Mapping[str, bool] | None = None,
    overrides: Mapping[str, bool] | None = None,
) -> dict[str, bool]:
    flags = dict(base or {})
    for name, enabled in dict(overrides or {}).items():
        flags[name] = bool(enabled)
    return flags


def build_runtime_config(
    *,
    settings: RuntimeSettings | None = None,
    features: Mapping[str, bool] | None = None,
    agents: Sequence[str] | None = None,
    metadata: Mapping[str, object] | None = None,
    governance_policy: str = DEFAULT_POLICY,
) -> RuntimeConfig:
    resolved_settings = settings or RuntimeSettings.from_env()
    resolved_features = merge_feature_flags(
        {
            "adaptive_ui": True,
            "cloud_governance": True,
            "hardware_bridge": resolved_settings.hardware_enabled,
            "message_bus": True,
        },
        features,
    )
    resolved_agents = tuple(agents or DEFAULT_AGENT_NAMES)
    resolved_metadata = {
        "environment": resolved_settings.environment,
        "provider": resolved_settings.model_provider,
        "model": resolved_settings.model_name,
    }
    resolved_metadata.update(dict(metadata or {}))
    return RuntimeConfig(
        settings=resolved_settings,
        features=resolved_features,
        agents=resolved_agents,
        governance_policy=governance_policy,
        metadata=resolved_metadata,
    )


__all__ = [
    "RuntimeConfig",
    "build_runtime_config",
    "load_config",
    "merge_feature_flags",
]
