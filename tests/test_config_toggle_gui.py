# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Config Toggle Gui module (tests)

import json

from hueyos.config_toggle_gui import update_toggle_settings


def test_update_toggle_settings(tmp_path):
    cfg = tmp_path / "cfg.json"
    cfg.write_text("{}")
    update_toggle_settings(cfg, {"foo": True})
    data = json.loads(cfg.read_text())
    assert data["foo"] is True
