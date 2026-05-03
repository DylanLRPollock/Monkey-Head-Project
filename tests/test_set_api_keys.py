import json
from pathlib import Path

from src.huey.memory.PY import set_api_keys


def test_prompt_keys_prefers_env_var(monkeypatch):
    data = {}
    monkeypatch.setenv("OPENAI_API_KEY", "env-secret")
    monkeypatch.setattr("builtins.input", lambda _prompt: "should-not-be-used")

    set_api_keys.prompt_keys(["openai"], data)

    assert data == {}


def test_save_config_ignores_empty_values(tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    monkeypatch.setattr(set_api_keys, "CONFIG_PATH", str(cfg))

    wrote = set_api_keys.save_config({"api_key": "", "api_key_google": "   "})

    assert wrote is False
    assert not cfg.exists()


def test_save_config_writes_non_empty_values(tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    monkeypatch.setattr(set_api_keys, "CONFIG_PATH", str(cfg))

    wrote = set_api_keys.save_config({"api_key": "secret", "api_key_google": ""})

    assert wrote is True
    saved = json.loads(Path(cfg).read_text(encoding="utf-8"))
    assert saved == {"api_key": "secret"}
