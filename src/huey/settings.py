"""Environment-driven runtime settings for HueyOS."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Self

from .constants import (
    DEFAULT_BOOT_PROFILE,
    DEFAULT_ENVIRONMENT,
    DEFAULT_HOST,
    DEFAULT_LOG_LEVEL,
    DEFAULT_PORT,
    DEFAULT_STORAGE_ROOT,
)


def _as_bool(value: object, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if not text:
        return default
    return text in {"1", "true", "yes", "on", "enabled"}


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    """Typed settings shared across the speculative subsystem tree."""

    environment: str = DEFAULT_ENVIRONMENT
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    debug: bool = False
    boot_profile: str = DEFAULT_BOOT_PROFILE
    storage_root: Path = Path(DEFAULT_STORAGE_ROOT)
    log_level: str = DEFAULT_LOG_LEVEL
    model_provider: str = "local"
    model_name: str = "spark-4-sim"
    allow_remote_control: bool = False
    hardware_enabled: bool = True

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> Self:
        env = dict(os.environ if environ is None else environ)
        return cls(
            environment=env.get("HUEY_ENV", DEFAULT_ENVIRONMENT),
            host=env.get("HUEY_HOST", DEFAULT_HOST),
            port=int(env.get("HUEY_PORT", str(DEFAULT_PORT))),
            debug=_as_bool(env.get("HUEY_DEBUG")),
            boot_profile=env.get("HUEY_BOOT_PROFILE", DEFAULT_BOOT_PROFILE),
            storage_root=Path(env.get("HUEY_STORAGE_ROOT", DEFAULT_STORAGE_ROOT)),
            log_level=env.get("HUEY_LOG_LEVEL", DEFAULT_LOG_LEVEL).upper(),
            model_provider=env.get("HUEY_MODEL_PROVIDER", "local"),
            model_name=env.get("HUEY_MODEL_NAME", "spark-4-sim"),
            allow_remote_control=_as_bool(env.get("HUEY_ALLOW_REMOTE_CONTROL")),
            hardware_enabled=_as_bool(env.get("HUEY_HARDWARE_ENABLED"), default=True),
        )

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["storage_root"] = str(self.storage_root)
        return payload


__all__ = ["RuntimeSettings"]
