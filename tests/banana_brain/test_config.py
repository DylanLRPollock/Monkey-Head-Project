"""Configuration loading, coercion, validation, and secret handling."""

from __future__ import annotations

import pytest

from huey.banana_brain.config import (
    BananaBrainConfig,
    ConfigError,
    _expand_env,
    _to_bool,
    _validate_bind,
    _validate_url,
    load_config,
)


def test_defaults_nested_sections_coercion_and_redaction():
    defaults = BananaBrainConfig.from_dict({})
    assert defaults.api_socket_path is not None
    assert defaults.to_dict()["api_token"] is None
    config = BananaBrainConfig.from_dict(
        {
            "gpu": {"poll_interval_seconds": "1.5", "device_uuid": "GPU-abc"},
            "priority": {"aging_step": "3"},
            "ollama": {"unload_pinned": "yes", "base_url": "https://ollama.local"},
            "storage": {"database_path": "./db.sqlite"},
            "api": {"token": "a-secret-token-123456"},
            "extra": {"deployment": "test"},
        }
    )
    assert config.poll_interval_seconds == 1.5
    assert config.priority_aging_step == 3
    assert config.ollama_unload_pinned is True
    assert str(config.database_path) == "db.sqlite"
    assert config.to_dict()["api_token"] == "***redacted***"
    assert config.to_dict(redact_secrets=False)["api_token"] == "a-secret-token-123456"
    with pytest.raises((AttributeError, TypeError)):
        config.poll_interval_seconds = 4


def test_flatten_collisions_unknown_keys_and_value_types():
    assert BananaBrainConfig.from_dict(None).api_socket_path is not None
    with pytest.raises(ConfigError, match="specified both"):
        BananaBrainConfig.from_dict(
            {"poll_interval_seconds": 3, "gpu": {"poll_interval_seconds": 2}}
        )
    with pytest.raises(ConfigError, match="specified both"):
        BananaBrainConfig.from_dict(
            {"priority_aging_step": 1, "priority": {"aging_step": 2}}
        )
    with pytest.raises(ConfigError, match="top-level YAML must be a mapping"):
        BananaBrainConfig.from_dict(["bad"])
    with pytest.raises(ConfigError, match="non-string YAML key"):
        BananaBrainConfig.from_dict({1: "bad"})
    with pytest.raises(ConfigError, match="unknown key"):
        BananaBrainConfig.from_dict({"surprise": True})
    with pytest.raises(ConfigError, match="extra must be a mapping"):
        BananaBrainConfig.from_dict({"extra": "bad"})
    with pytest.raises(ConfigError, match="expected int, got bool"):
        BananaBrainConfig.from_dict({"priority_aging_step": True})
    with pytest.raises(ConfigError, match="expected int"):
        BananaBrainConfig.from_dict({"priority_aging_step": "bad"})
    with pytest.raises(ConfigError, match="expected number, got bool"):
        BananaBrainConfig.from_dict({"poll_interval_seconds": True})
    with pytest.raises(ConfigError, match="expected number"):
        BananaBrainConfig.from_dict({"poll_interval_seconds": "bad"})
    with pytest.raises(ConfigError, match="expected bool"):
        BananaBrainConfig.from_dict({"ollama_unload_pinned": "perhaps"})
    assert _to_bool("flag", " OFF ", source="test") is False
    assert _to_bool("flag", "on", source="test") is True
    assert _to_bool("flag", True, source="test") is True


def test_environment_expansion_and_loader_errors(tmp_path, monkeypatch):
    monkeypatch.setenv("BB_TOKEN", "0123456789abcdef")
    assert _expand_env(
        {"api": {"token": "${BB_TOKEN}"}, "a": ["${BB_TOKEN}"]}, source="test"
    ) == {"api": {"token": "0123456789abcdef"}, "a": ["0123456789abcdef"]}
    with pytest.raises(ConfigError, match="not set in the environment"):
        _expand_env("${MISSING_BB_TOKEN}", source="test")
    with pytest.raises(ConfigError, match="config file not found"):
        load_config(tmp_path / "missing.yaml")
    with pytest.raises(ConfigError, match="not a file"):
        load_config(tmp_path)
    empty = tmp_path / "empty.yaml"
    empty.write_text("\n")
    assert load_config(empty).poll_interval_seconds == 2.0
    malformed = tmp_path / "malformed.yaml"
    malformed.write_text("bad: [\n")
    with pytest.raises(ConfigError, match="invalid YAML at line"):
        load_config(malformed)
    sequence = tmp_path / "sequence.yaml"
    sequence.write_text("- one\n- two\n")
    with pytest.raises(ConfigError, match="top-level YAML must be a mapping"):
        load_config(sequence)
    null_yaml = tmp_path / "null.yaml"
    null_yaml.write_text("null\n")
    assert load_config(null_yaml).poll_interval_seconds == 2.0
    valid = tmp_path / "valid.yaml"
    valid.write_text("api:\n  token: ${BB_TOKEN}\n")
    assert load_config(valid).api_token == "0123456789abcdef"


def test_validation_collects_all_policy_violations():
    with pytest.raises(ConfigError) as exc:
        BananaBrainConfig.from_dict(
            {
                "shutdown_grace_seconds": 0,
                "device_uuid": "bad",
                "poll_interval_seconds": 5,
                "max_staleness_seconds": 1,
                "vram_headroom_gib": -1,
                "vram_headroom_percent": 1,
                "priority_aging_interval_seconds": -1,
                "priority_aging_step": -1,
                "priority_aging_cap": 0,
                "priority_overdue_boost": -1,
                "ollama_base_url": "ftp://bad",
                "comfyui_base_url": "http:///missing-host",
                "ollama_request_timeout_seconds": 1,
                "ollama_connect_timeout_seconds": 2,
                "comfyui_poll_interval_seconds": 0,
                "comfyui_job_timeout_seconds": 1,
                "comfyui_connect_timeout_seconds": 2,
                "watchdog_stuck_job_seconds": 0,
                "watchdog_temperature_ceiling_c": 0,
                "comfyui_inference_overhead_gib": -1,
                "api_bind": "0.0.0.0:0",
            }
        )
    details = str(exc.value)
    for expected in [
        "shutdown_grace_seconds",
        "device_uuid",
        "max_staleness_seconds",
        "vram_headroom_gib",
        "priority_aging_cap",
        "ollama_base_url",
        "api_token is required",
        "must not use wildcard address 0.0.0.0",
    ]:
        assert expected in details


def test_ipv6_wildcard_bind_is_rejected():
    with pytest.raises(ConfigError, match="wildcard address ::"):
        BananaBrainConfig.from_dict(
            {
                "api_bind": "[::]:8080",
                "api_token": "0123456789abcdef",
            }
        )


def test_bind_and_url_validation_variants():
    assert _validate_bind("") == "empty"
    assert "socket path" in _validate_bind("/tmp/api.sock")
    assert "host:port" in _validate_bind("localhost")
    assert "missing host" in _validate_bind(":80")
    assert "invalid port" in _validate_bind("localhost:abc")
    assert "out of range" in _validate_bind("localhost:65536")
    assert _validate_bind("localhost:8080") is None
    assert "scheme" in _validate_url("ftp://host")
    assert "hostname" in _validate_url("http://")
    assert _validate_url("https://host:443/path") is None
    assert "invalid URL" in _validate_url("https://host:99999")


def test_validation_reports_short_tokens_and_nonpositive_monitor_limits():
    with pytest.raises(ConfigError) as exc:
        BananaBrainConfig.from_dict(
            {
                "api_bind": "127.0.0.1:8080",
                "api_token": "short",
                "poll_interval_seconds": 0,
                "max_staleness_seconds": 0,
            }
        )
    details = str(exc.value)
    assert "api_token must be at least 16 characters" in details
    assert "poll_interval_seconds must be > 0" in details
    assert "max_staleness_seconds must be > 0" in details
