"""Cover config loading, nested lookup, merge, and persistence edge paths."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from huey.config_manager import ConfigManager


def test_config_manager_loads_json_ini_defaults_and_empty_content(tmp_path):
    json_path = tmp_path / "settings.json"
    json_path.write_text('{"runtime": {"mode": "local"}}', encoding="utf-8")
    manager = ConfigManager(json_path)
    assert manager.get_setting("runtime.mode") == "local"
    assert manager.get_setting("runtime.missing", "fallback") == "fallback"
    assert manager.get_setting("runtime.mode.child", "fallback") == "fallback"
    assert manager.get_setting("") == manager.as_dict()
    assert manager.get_setting("", "fallback") == manager.as_dict()

    ini_path = tmp_path / "settings.ini"
    ini_path.write_text(
        "[runtime]\nmode = local\n[DEFAULT]\nregion = north\n", encoding="utf-8"
    )
    ini = ConfigManager(ini_path)
    assert ini.get_section("runtime") == {"mode": "local", "region": "north"}
    assert ini.get_section("absent", {"value": 1}) == {"value": 1}

    plain_ini_path = tmp_path / "plain.ini"
    plain_ini_path.write_text("[plain]\nkey = value\n", encoding="utf-8")
    assert ConfigManager(plain_ini_path).get_section("plain") == {"key": "value"}

    empty = tmp_path / "empty.cfg"
    empty.write_text("  \n", encoding="utf-8")
    assert ConfigManager(empty).as_dict() == {}
    assert ConfigManager(tmp_path / "missing.json").as_dict() == {}


def test_config_manager_handles_unreadable_and_non_mapping_sections(
    tmp_path, monkeypatch
):
    path = tmp_path / "unreadable.json"
    path.write_text("{}", encoding="utf-8")
    manager = ConfigManager(path)
    original_read_text = Path.read_text

    def read_with_error(current, *args, **kwargs):
        if current == path:
            raise PermissionError("denied")
        return original_read_text(current, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_with_error)
    assert manager._load() == {}

    manager._data = {"section": "plain text"}
    assert manager.get_section("section", {"fallback": True}) == {"fallback": True}


def test_config_path_resolution_honors_environment_and_legacy_fallbacks(
    monkeypatch, tmp_path
):
    manager = ConfigManager(tmp_path / "explicit.json")
    monkeypatch.setenv("MONKEY_HEAD_CONFIG", str(tmp_path / "from-env.json"))
    assert manager._resolve_path(None) == tmp_path / "from-env.json"
    monkeypatch.delenv("MONKEY_HEAD_CONFIG")

    original_exists = Path.exists

    def no_legacy_config(path):
        if path.name == "main.config":
            return False
        return original_exists(path)

    monkeypatch.setattr(Path, "exists", no_legacy_config)
    fallback = manager._resolve_path(None)
    assert fallback.parts[-4:] == ("src", "huey", "config", "main.config")

    def legacy_config_exists(path):
        if path.name == "main.config":
            return path.parent.name == "config"
        return original_exists(path)

    monkeypatch.setattr(Path, "exists", legacy_config_exists)
    legacy = manager._resolve_path(None)
    assert legacy.parts[-2:] == ("config", "main.config")


def test_config_manager_nested_updates_replace_scalars_and_return_copies(tmp_path):
    path = tmp_path / "nested.json"
    manager = ConfigManager(path)
    manager.set_setting("runtime", "old")
    manager.set_setting("runtime.mode", "local")
    manager.set_setting("runtime.nested.enabled", True)
    manager.update_settings({"runtime": {"nested": {"count": 2}}, "new": 3})
    assert manager.get_setting("runtime") == {
        "mode": "local",
        "nested": {"enabled": True, "count": 2},
    }
    assert json.loads(path.read_text(encoding="utf-8")) == manager.as_dict()

    snapshot = manager.as_dict()
    snapshot["runtime"]["mode"] = "mutated"
    assert manager.get_setting("runtime.mode") == "local"
    with pytest.raises(ValueError, match="key must not be empty"):
        manager.set_setting("", 1)
