"""Cover JSON, INI, nested-key, and compatibility paths in ConfigManager."""

from __future__ import annotations

from pathlib import Path

from huey.memory.PY import config_manager


def test_config_path_resolution_and_format_selection(tmp_path, monkeypatch):
    explicit = tmp_path / "custom.json"
    assert config_manager.ConfigManager._resolve_path(explicit) == explicit.resolve()
    monkeypatch.setenv("MONKEY_HEAD_CONFIG", str(explicit))
    assert config_manager.ConfigManager._resolve_path(None) == explicit.resolve()
    monkeypatch.delenv("MONKEY_HEAD_CONFIG")
    memory_root = tmp_path / "memory"
    monkeypatch.setattr(config_manager, "get_memory_path", lambda create: memory_root)
    assert (
        config_manager.ConfigManager._resolve_path(None)
        == (memory_root / config_manager.DEFAULT_CONFIG).resolve()
    )
    assert config_manager.ConfigManager._detect_format(Path("data.INI")) == "ini"
    assert config_manager.ConfigManager._detect_format(Path("data.cfg")) == "ini"
    assert config_manager.ConfigManager._detect_format(Path("data.json")) == "json"


def test_json_load_save_nested_and_flattened_sections(tmp_path):
    path = tmp_path / "config.json"
    manager = config_manager.ConfigManager(path)
    assert manager.config == {}
    assert manager.get_setting("missing.value", "fallback") == "fallback"
    assert manager.get_section("missing", {"enabled": False}) == {"enabled": False}

    manager.update_settings(
        {"runtime": {"enabled": True, "workers": 2}, "gui.color": "blue"}
    )
    assert manager.get_setting("runtime.enabled") is True
    assert manager.get_setting("runtime.workers") == 2
    assert manager.get_setting("runtime", "fallback") == {"enabled": True, "workers": 2}
    assert manager.get_section("runtime", {"enabled": False, "mode": "safe"}) == {
        "enabled": True,
        "mode": "safe",
        "workers": 2,
    }
    assert manager.get_section("gui", {"enabled": False}) == {
        "enabled": False,
        "color": "blue",
    }

    manager.set_setting("new.value", 3)
    reloaded = config_manager.ConfigManager(path)
    assert reloaded.config["new.value"] == 3
    assert reloaded.get_setting("gui.color") == "blue"


def test_json_loader_handles_invalid_and_non_object_documents(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("not json", encoding="utf-8")
    assert config_manager.ConfigManager(path).config == {}
    path.write_text("[1, 2]", encoding="utf-8")
    assert config_manager.ConfigManager(path).config == {}


def test_ini_load_and_save_support_defaults_sections_and_scalars(tmp_path):
    path = tmp_path / "settings.ini"
    path.write_text(
        "[DEFAULT]\nmode = safe\n[network]\nhost = localhost\n", encoding="utf-8"
    )
    manager = config_manager.ConfigManager(path)
    assert manager.get_setting("mode") == "safe"
    assert manager.get_section("network") == {"mode": "safe", "host": "localhost"}
    manager.update_settings(
        {"network": {"host": "example.test", "port": 9000}, "enabled": True}
    )
    reloaded = config_manager.ConfigManager(path)
    assert reloaded.get_setting("network.host") == "example.test"
    assert reloaded.get_setting("enabled") == "True"
    assert reloaded.get_section("network", {"tls": "on"}) == {
        "tls": "on",
        "mode": "safe",
        "enabled": "True",
        "host": "example.test",
        "port": "9000",
    }
