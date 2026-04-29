# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test License Gui module (tests)

import json
from datetime import datetime

from hueyos.license_gui import accept_license


def test_accept_license_updates_config(tmp_path):
    config_path = tmp_path / "test_config.json"
    config_path.write_text(json.dumps({"license.accepted": False}), encoding="utf-8")

    accept_license(config_path, "dummy-hash")

    updated = json.loads(config_path.read_text(encoding="utf-8"))
    accepted_at = datetime.fromisoformat(updated["license.accepted_at"])

    assert updated["license.accepted"] is True
    assert accepted_at.tzinfo is not None
    assert updated["license.hash"] == "dummy-hash"


def test_accept_license_preserves_existing_settings(tmp_path):
    config_path = tmp_path / "nested" / "gui_config.json"
    config_path.parent.mkdir()
    config_path.write_text(
        json.dumps({"theme": "dark", "license.accepted": False}),
        encoding="utf-8",
    )

    accept_license(config_path, "license-hash")

    updated = json.loads(config_path.read_text(encoding="utf-8"))
    assert updated["theme"] == "dark"
    assert updated["license.accepted"] is True
    assert updated["license.hash"] == "license-hash"


def test_accept_license_creates_missing_config_file(tmp_path):
    config_path = tmp_path / "new" / "gui_config.json"

    accept_license(config_path, "new-hash")

    updated = json.loads(config_path.read_text(encoding="utf-8"))
    assert updated["license.accepted"] is True
    assert updated["license.hash"] == "new-hash"
