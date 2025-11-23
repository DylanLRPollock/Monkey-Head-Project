# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test License Cli module (tests)

import json
from unittest.mock import patch

import pytest

from hueyos.license_cli import show_license_cli


def test_license_decline(tmp_path):
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"license.accepted": False}))

    with patch("hueyos.license_cli.prompt_response", return_value="no"):
        with pytest.raises(RuntimeError):
            show_license_cli(cfg)

    data = json.loads(cfg.read_text())
    assert data.get("license.accepted") is False
