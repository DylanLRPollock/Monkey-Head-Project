import json
from monkey_head.config_toggle_gui import update_toggle_settings


def test_update_toggle_settings(tmp_path):
    cfg = tmp_path / "cfg.json"
    cfg.write_text("{}")
    update_toggle_settings(cfg, {"foo": True})
    data = json.loads(cfg.read_text())
    assert data["foo"] is True
