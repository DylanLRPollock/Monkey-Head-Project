# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Config Manager module (tests)

from hueyos.config_manager import ConfigManager


def test_config_manager_roundtrip(tmp_path):
    cfg = tmp_path / "cfg.json"
    manager = ConfigManager(str(cfg))
    manager.set_setting("foo", 1)
    assert cfg.exists()
    loaded = ConfigManager(str(cfg))
    assert loaded.get_setting("foo") == 1


def test_config_manager_default(tmp_path):
    cfg = tmp_path / "missing.json"
    manager = ConfigManager(str(cfg))
    assert manager.get_setting("unknown", "default") == "default"


def test_update_settings(tmp_path):
    cfg = tmp_path / "cfg.json"
    manager = ConfigManager(str(cfg))
    manager.update_settings({"a": 1, "b": 2})
    loaded = ConfigManager(str(cfg))
    assert loaded.get_setting("a") == 1
    assert loaded.get_setting("b") == 2
