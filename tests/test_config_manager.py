from monkey_head.config_manager import ConfigManager


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
