"""
banana_brain.config — Banana Brain configuration loader and validator.

Responsibilities (from the Banana Brain design doc):
  * Load banana-brain.yaml.
  * Validate device selection, GPU budgets, scheduling policy, service
    endpoints, API exposure, and cross-field invariants.
  * Provide an immutable config object that every component can share
    without locking.

Public API:

  load_config(path)               -> BananaBrainConfig
  BananaBrainConfig.from_dict(d)  -> BananaBrainConfig
  BananaBrainConfig.to_dict()     -> dict  (secrets redacted by default)

  ConfigError                     raised with the full list of problems

Shape of the YAML file (all keys optional; safe defaults apply):

  # ---- Top-level -------------------------------------------------------
  shutdown_grace_seconds: 30
  device: "V100"

  # ---- GPU / device ----------------------------------------------------
  device_uuid: "GPU-xxxxxxxx-..."; # preferred identity
  pci_bus_id: "0000:01:00.0";      # alternative identity
  poll_interval_seconds: 2.0
  max_staleness_seconds: 5.0

  # ---- VRAM budget -----------------------------------------------------
  vram_headroom_gib: 3.0
  vram_headroom_percent: 0.0

  # ---- Priority --------------------------------------------------------
  priority_aging_interval_seconds: 60
  priority_aging_step: 1
  priority_aging_cap: 99
  priority_overdue_boost: 20

  # ---- Ollama ----------------------------------------------------------
  ollama_base_url: "http://127.0.0.1:11434"
  ollama_keep_alive: "5m"
  ollama_request_timeout_seconds: 600
  ollama_connect_timeout_seconds: 10
  ollama_unload_pinned: false
  ollama_unload_lru_first: true

  # ---- ComfyUI ---------------------------------------------------------
  comfyui_base_url: "http://127.0.0.1:8188"
  comfyui_poll_interval_seconds: 0.75
  comfyui_job_timeout_seconds: 900
  comfyui_connect_timeout_seconds: 10
  comfyui_inference_overhead_gib: 3.0

  # ---- Storage ---------------------------------------------------------
  database_path: "data/banana-brain.db"

  # ---- Local control API -----------------------------------------------
  api_socket_path: "data/banana-brain.sock"  # default if api_bind is unset
  api_bind: "127.0.0.1:8080"                 # optional TCP (requires token)
  api_token: "${BANANA_BRAIN_TOKEN}"         # env-var expansion supported

  # ---- Watchdog --------------------------------------------------------
  watchdog_stuck_job_seconds: 1800
  watchdog_temperature_ceiling_c: 85

  # ---- Free-form, accessible via config.extra --------------------------
  extra:
    deployment_id: "hueyos-prod-1"

Any of the above may alternatively appear nested, e.g.:

  ollama:
    base_url: "http://127.0.0.1:11434"

Nested and flat forms are equivalent; the loader normalises both to the
same flat attributes. Mixing the two forms for the same field is an error.

String values support ${ENV_VAR} expansion. Undefined variables are a
validation error, so a missing secret fails at startup, not at first use.
"""

from __future__ import annotations

import ipaddress
import logging
import os
import re
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

__all__ = [
    "BananaBrainConfig",
    "ConfigError",
    "load_config",
]

LOG = logging.getLogger("banana_brain.config")


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ConfigError(RuntimeError):
    """
    Raised when the config file cannot be loaded or fails validation.

    `.problems` is a list of human-readable messages; the string form
    joins them with semicolons so callers can log a single line.
    """

    def __init__(self, problems: str | list[str]) -> None:
        self.problems: list[str] = (
            [problems] if isinstance(problems, str) else list(problems)
        )
        super().__init__("; ".join(self.problems))


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

#: Top-level YAML sections whose contents are flattened into the dataclass
#: as ``<section>_<key>``. Everything else at the top level must match a
#: dataclass field name directly (or be ``extra``).
_KNOWN_SECTIONS: frozenset[str] = frozenset(
    {"gpu", "priority", "ollama", "comfyui", "storage", "api", "watchdog"}
)

_PATH_FIELDS: frozenset[str] = frozenset({"database_path", "api_socket_path"})
_INT_FIELDS: frozenset[str] = frozenset(
    {"priority_aging_step", "priority_aging_cap", "priority_overdue_boost"}
)
_FLOAT_FIELDS: frozenset[str] = frozenset(
    {
        "shutdown_grace_seconds",
        "poll_interval_seconds",
        "max_staleness_seconds",
        "vram_headroom_gib",
        "vram_headroom_percent",
        "priority_aging_interval_seconds",
        "ollama_request_timeout_seconds",
        "ollama_connect_timeout_seconds",
        "comfyui_poll_interval_seconds",
        "comfyui_job_timeout_seconds",
        "comfyui_connect_timeout_seconds",
        "comfyui_inference_overhead_gib",
        "watchdog_stuck_job_seconds",
        "watchdog_temperature_ceiling_c",
    }
)
_BOOL_FIELDS: frozenset[str] = frozenset(
    {"ollama_unload_pinned", "ollama_unload_lru_first"}
)
_STR_FIELDS: frozenset[str] = frozenset(
    {
        "device",
        "device_uuid",
        "pci_bus_id",
        "ollama_base_url",
        "ollama_keep_alive",
        "comfyui_base_url",
        "api_bind",
        "api_token",
    }
)

#: Secret fields that to_dict() redacts by default.
_SECRET_FIELDS: frozenset[str] = frozenset({"api_token"})

#: Every field name the dataclass exposes except `extra`. Used to reject
#: unknown keys after flattening.
_KNOWN_FIELDS: frozenset[str] = (
    _PATH_FIELDS | _INT_FIELDS | _FLOAT_FIELDS | _BOOL_FIELDS | _STR_FIELDS | {"extra"}
)


# ---------------------------------------------------------------------------
# Immutable config object
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BananaBrainConfig:
    """
    Validated Banana Brain configuration.

    Construct directly (for tests) with keyword arguments, or via
    load_config() / from_dict(). All fields default to values that make
    the system safe on a single-GPU workstation.

    Frozen: use dataclasses.replace() to derive a modified copy.
    """

    # ---- Lifecycle --------------------------------------------------------
    shutdown_grace_seconds: float = 30.0
    device: str | None = None

    # ---- GPU / monitor ----------------------------------------------------
    device_uuid: str | None = None
    pci_bus_id: str | None = None
    poll_interval_seconds: float = 2.0
    max_staleness_seconds: float = 5.0

    # ---- VRAM -------------------------------------------------------------
    vram_headroom_gib: float = 3.0
    vram_headroom_percent: float = 0.0

    # ---- Priority ---------------------------------------------------------
    priority_aging_interval_seconds: float = 60.0
    priority_aging_step: int = 1
    priority_aging_cap: int = 99
    priority_overdue_boost: int = 20

    # ---- Ollama -----------------------------------------------------------
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_keep_alive: str = "5m"
    ollama_request_timeout_seconds: float = 600.0
    ollama_connect_timeout_seconds: float = 10.0
    ollama_unload_pinned: bool = False
    ollama_unload_lru_first: bool = True

    # ---- ComfyUI ----------------------------------------------------------
    comfyui_base_url: str = "http://127.0.0.1:8188"
    comfyui_poll_interval_seconds: float = 0.75
    comfyui_job_timeout_seconds: float = 900.0
    comfyui_connect_timeout_seconds: float = 10.0
    comfyui_inference_overhead_gib: float = 3.0

    # ---- Storage ----------------------------------------------------------
    database_path: Path = Path("data/banana-brain.db")

    # ---- Control API ------------------------------------------------------
    api_socket_path: Path | None = None
    api_bind: str | None = None
    api_token: str | None = field(default=None, repr=False)

    # ---- Watchdog ---------------------------------------------------------
    watchdog_stuck_job_seconds: float = 1800.0
    watchdog_temperature_ceiling_c: float = 85.0

    # ---- Free-form --------------------------------------------------------
    extra: dict[str, Any] = field(default_factory=dict, compare=False)

    # ------------------------------------------------------------------
    # Post-init: safe defaults that depend on other fields
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:
        # Secure-by-default: if neither a Unix socket nor a TCP bind is
        # configured, use the Unix socket. Every API deployment then has
        # at least one working transport, and the TCP path (which requires
        # a token) is strictly opt-in.
        if self.api_socket_path is None and self.api_bind is None:
            object.__setattr__(self, "api_socket_path", Path("data/banana-brain.sock"))

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self, *, redact_secrets: bool = True) -> dict[str, Any]:
        """Return a plain-dict view, safe for logging and diagnostics."""
        result: dict[str, Any] = {}
        for f in fields(self):
            value = getattr(self, f.name)
            if f.name in _SECRET_FIELDS and redact_secrets and value:
                value = "***redacted***"
            elif isinstance(value, Path):
                value = str(value)
            result[f.name] = value
        return result

    @classmethod
    def from_dict(
        cls, data: dict[str, Any], *, source: str = "<dict>"
    ) -> BananaBrainConfig:
        """
        Build a config from a (possibly nested) mapping.

        The mapping must already be free of ${ENV_VAR} references —
        load_config() expands them before calling here. This keeps
        from_dict pure and testable.
        """
        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise ConfigError(
                f"{source}: top-level YAML must be a mapping, "
                f"got {type(data).__name__}"
            )
        flat = _flatten(data, source=source)
        coerced = _coerce(flat, source=source)

        extra = coerced.pop("extra", None) or {}
        if not isinstance(extra, dict):
            raise ConfigError(
                f"{source}: extra must be a mapping, got {type(extra).__name__}"
            )

        unknown = set(coerced) - _KNOWN_FIELDS
        if unknown:
            raise ConfigError(
                f"{source}: unknown key(s): "
                + ", ".join(sorted(unknown))
                + " (put deployment-specific fields under extra:)"
            )

        try:
            cfg = cls(**coerced, extra=dict(extra))
        except TypeError as exc:
            raise ConfigError(f"{source}: {exc}") from exc

        problems = _validate(cfg)
        if problems:
            raise ConfigError(problems)
        return cfg


# ---------------------------------------------------------------------------
# Public loader
# ---------------------------------------------------------------------------


def load_config(path: str | Path) -> BananaBrainConfig:
    """
    Load and validate a YAML config file.

    A missing file is an error. An empty file yields all defaults. YAML
    syntax errors are reported with line/column information where available.
    """
    cfg_path = Path(path).expanduser()
    raw = _read_yaml_mapping(cfg_path)
    expanded = _expand_env(raw, source=str(cfg_path))
    cfg = BananaBrainConfig.from_dict(expanded, source=str(cfg_path))

    LOG.info(
        "loaded config from %s (device_uuid=%s, pci_bus_id=%s, " "database=%s, api=%s)",
        cfg_path,
        cfg.device_uuid or "-",
        cfg.pci_bus_id or "-",
        cfg.database_path,
        (
            f"tcp {cfg.api_bind}"
            if cfg.api_bind
            else (f"socket {cfg.api_socket_path}" if cfg.api_socket_path else "none")
        ),
    )
    return cfg


def _read_yaml_mapping(cfg_path: Path) -> dict[str, Any]:
    if not cfg_path.exists():
        raise ConfigError(f"config file not found: {cfg_path}")
    if not cfg_path.is_file():
        raise ConfigError(f"config path is not a file: {cfg_path}")

    try:
        text = cfg_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"cannot read {cfg_path}: {exc}") from exc

    return _parse_yaml_mapping(text, cfg_path)


def _parse_yaml_mapping(text: str, cfg_path: Path) -> dict[str, Any]:
    try:
        import yaml  # PyYAML
    except ImportError as exc:
        raise ConfigError(
            "PyYAML is required to load config files; pip install pyyaml"
        ) from exc

    try:
        raw = yaml.safe_load(text) if text.strip() else {}
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        where = (
            f" at line {mark.line + 1}, column {mark.column + 1}"
            if mark is not None
            else ""
        )
        raise ConfigError(f"{cfg_path}: invalid YAML{where}: {exc}") from exc

    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ConfigError(
            f"{cfg_path}: top-level YAML must be a mapping, "
            f"got {type(raw).__name__}"
        )

    return raw


# ---------------------------------------------------------------------------
# Flattening: nested YAML -> flat dict
# ---------------------------------------------------------------------------


def _flatten(data: dict[str, Any], *, source: str, prefix: str = "") -> dict[str, Any]:
    """
    Flatten known sections to ``section_key``. Unknown top-level keys are
    preserved verbatim so the caller can reject them with a clear message.
    """
    out: dict[str, Any] = {}
    for key, value in data.items():
        if not isinstance(key, str):
            raise ConfigError(f"{source}: non-string YAML key {key!r}; quote keys")
        # GPU and storage keys are already named after their flat config
        # fields (for example ``gpu.poll_interval_seconds`` and
        # ``storage.database_path``). Other sections use namespaced fields.
        flat_key = (
            key if not prefix or prefix in {"gpu", "storage"} else f"{prefix}_{key}"
        )

        if not prefix and key in _KNOWN_SECTIONS and isinstance(value, dict):
            nested = _flatten(value, source=source, prefix=key)
            for nk, nv in nested.items():
                if nk in out:
                    raise ConfigError(
                        f"{source}: {nk!r} specified both as "
                        f"a flat key and inside section {key!r}; pick one"
                    )
                out[nk] = nv
            continue

        if flat_key in out:
            raise ConfigError(f"{source}: duplicate key {flat_key!r}")
        out[flat_key] = value
    return out


# ---------------------------------------------------------------------------
# Environment expansion
# ---------------------------------------------------------------------------

_ENV_VAR_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _expand_env(value: Any, *, source: str) -> Any:
    """
    Recursively substitute ``${NAME}`` in string values.

    An undefined variable is a validation error: the missing secret should
    surface at startup, not on first API call.
    """
    if isinstance(value, str):

        def repl(match: re.Match[str]) -> str:
            name = match.group(1)
            if name not in os.environ:
                raise ConfigError(
                    f"{source}: ${{{name}}} is referenced but not set in "
                    f"the environment"
                )
            return os.environ[name]

        return _ENV_VAR_RE.sub(repl, value)
    if isinstance(value, dict):
        return {k: _expand_env(v, source=source) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env(v, source=source) for v in value]
    return value


# ---------------------------------------------------------------------------
# Type coercion
# ---------------------------------------------------------------------------


def _coerce(flat: dict[str, Any], *, source: str) -> dict[str, Any]:
    """Coerce scalars to their declared types with clear error messages."""
    return {
        key: _coerce_value(key, value, source=source) for key, value in flat.items()
    }


def _coerce_value(key: str, value: Any, *, source: str) -> Any:
    if value is None:
        return None
    if key in _PATH_FIELDS:
        return Path(str(value))
    if key in _INT_FIELDS:
        return _coerce_int(key, value, source=source)
    if key in _FLOAT_FIELDS:
        return _coerce_float(key, value, source=source)
    if key in _BOOL_FIELDS:
        return _to_bool(key, value, source=source)
    if key in _STR_FIELDS:
        return str(value)
    # Unknown keys are preserved so from_dict can report them.
    return value


def _coerce_int(key: str, value: Any, *, source: str) -> int:
    if isinstance(value, bool):
        raise ConfigError(f"{source}: {key}: expected int, got bool")
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ConfigError(f"{source}: {key}: expected int, got {value!r}") from None


def _coerce_float(key: str, value: Any, *, source: str) -> float:
    if isinstance(value, bool):
        raise ConfigError(f"{source}: {key}: expected number, got bool")
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ConfigError(f"{source}: {key}: expected number, got {value!r}") from None


def _to_bool(key: str, value: Any, *, source: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    raise ConfigError(f"{source}: {key}: expected bool, got {value!r}")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _validate(cfg: BananaBrainConfig) -> list[str]:
    """
    Return a list of problems; empty list means valid.

    Collects every problem rather than failing on the first, so operators
    can fix a batch in one pass.
    """
    problems = []
    problems.extend(_validate_gpu_settings(cfg))
    problems.extend(_validate_vram_settings(cfg))
    problems.extend(_validate_priority_settings(cfg))
    problems.extend(_validate_service_settings(cfg))
    problems.extend(_validate_api_settings(cfg))
    return problems


def _validate_gpu_settings(cfg: BananaBrainConfig) -> list[str]:
    problems = []
    if cfg.shutdown_grace_seconds <= 0:
        problems.append("shutdown_grace_seconds must be > 0")
    if cfg.poll_interval_seconds <= 0:
        problems.append("poll_interval_seconds must be > 0")
    if cfg.max_staleness_seconds <= 0:
        problems.append("max_staleness_seconds must be > 0")
    if cfg.max_staleness_seconds < cfg.poll_interval_seconds:
        problems.append(
            f"max_staleness_seconds ({cfg.max_staleness_seconds}) must be "
            f">= poll_interval_seconds ({cfg.poll_interval_seconds})"
        )
    if cfg.device_uuid and not cfg.device_uuid.upper().startswith("GPU-"):
        problems.append(
            "device_uuid should start with 'GPU-' (NVML UUID format); "
            "verify with 'nvidia-smi -L'"
        )
    return problems


def _validate_vram_settings(cfg: BananaBrainConfig) -> list[str]:
    problems = []
    if cfg.vram_headroom_gib < 0:
        problems.append("vram_headroom_gib must be >= 0")
    if not (0.0 <= cfg.vram_headroom_percent < 1.0):
        problems.append("vram_headroom_percent must be in [0, 1)")
    if cfg.comfyui_inference_overhead_gib < 0:
        problems.append("comfyui_inference_overhead_gib must be >= 0")
    return problems


def _validate_priority_settings(cfg: BananaBrainConfig) -> list[str]:
    problems = []
    if cfg.priority_aging_interval_seconds < 0:
        problems.append("priority_aging_interval_seconds must be >= 0")
    if cfg.priority_aging_step < 0:
        problems.append("priority_aging_step must be >= 0")
    if not (1 <= cfg.priority_aging_cap <= 100):
        problems.append(
            f"priority_aging_cap ({cfg.priority_aging_cap}) must be in [1, 100]"
        )
    if cfg.priority_overdue_boost < 0:
        problems.append("priority_overdue_boost must be >= 0")
    return problems


def _validate_service_settings(cfg: BananaBrainConfig) -> list[str]:
    problems = []
    for name, url in (
        ("ollama_base_url", cfg.ollama_base_url),
        ("comfyui_base_url", cfg.comfyui_base_url),
    ):
        problem = _validate_url(url)
        if problem:
            problems.append(f"{name}: {problem}")
    timeout_fields = (
        "ollama_request_timeout_seconds",
        "ollama_connect_timeout_seconds",
        "comfyui_poll_interval_seconds",
        "comfyui_job_timeout_seconds",
        "comfyui_connect_timeout_seconds",
        "watchdog_stuck_job_seconds",
        "watchdog_temperature_ceiling_c",
    )
    for name in timeout_fields:
        if getattr(cfg, name) <= 0:
            problems.append(f"{name} must be > 0")
    if cfg.ollama_connect_timeout_seconds >= cfg.ollama_request_timeout_seconds:
        problems.append(
            "ollama_connect_timeout_seconds must be less than "
            "ollama_request_timeout_seconds"
        )
    if cfg.comfyui_connect_timeout_seconds >= cfg.comfyui_job_timeout_seconds:
        problems.append(
            "comfyui_connect_timeout_seconds must be less than "
            "comfyui_job_timeout_seconds"
        )
    return problems


def _validate_api_settings(cfg: BananaBrainConfig) -> list[str]:
    if not cfg.api_bind:
        return []
    problems = []
    problem = _validate_bind(cfg.api_bind)
    if problem:
        problems.append(f"api_bind: {problem}")
    if not cfg.api_token:
        problems.append(
            "api_token is required when api_bind is set; a TCP-exposed "
            "control API must require authentication"
        )
    elif len(cfg.api_token) < 16:
        problems.append("api_token must be at least 16 characters when api_bind is set")
    bind_host = cfg.api_bind.rpartition(":")[0].strip("[]")
    try:
        wildcard_bind = ipaddress.ip_address(bind_host).is_unspecified
    except ValueError:
        wildcard_bind = False
    if wildcard_bind:
        problems.append(
            f"api_bind must not use wildcard address {bind_host} without an explicit "
            "reverse-proxy in front; use 127.0.0.1 or a specific interface address"
        )
    return problems


def _validate_url(url: str) -> str | None:
    try:
        parsed = urlparse(url)
    except Exception as exc:
        return f"invalid URL {url!r}: {exc}"
    if parsed.scheme not in ("http", "https"):
        return f"scheme must be http or https, got {parsed.scheme!r}"
    if not parsed.hostname:
        return "missing hostname"
    try:
        port = parsed.port
    except ValueError as exc:
        return f"invalid URL {url!r}: {exc}"
    if port is not None and not (0 < port < 65536):
        return f"invalid port {port}"
    return None


def _validate_bind(bind: str) -> str | None:
    if not bind:
        return "empty"
    if bind.startswith("/"):
        return "looks like a socket path; use api_socket_path instead"
    host, sep, port_str = bind.rpartition(":")
    if not sep:
        return "expected 'host:port'"
    if not host:
        return "missing host"
    try:
        port = int(port_str)
    except ValueError:
        return f"invalid port {port_str!r}"
    if not (0 < port < 65536):
        return f"port out of range: {port}"
    return None
