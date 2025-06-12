# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from monkey_head.license_cli import show_license_cli


class TestLicenseCli(unittest.TestCase):
    def test_show_license_cli_accepts(self):
        temp_path = Path("/tmp/test_config_cli.json")
        data = {"license.accepted": False}
        with temp_path.open("w", encoding="utf-8") as f:
            json.dump(data, f)

        with patch("builtins.input", return_value="y"):
            show_license_cli(temp_path)

        with temp_path.open(encoding="utf-8") as f:
            updated = json.load(f)

        self.assertTrue(updated.get("license.accepted"))
        os.remove(temp_path)

    def test_show_license_cli_declines(self):
        temp_path = Path("/tmp/test_config_cli.json")
        with temp_path.open("w", encoding="utf-8") as f:
            json.dump({"license.accepted": False}, f)

        with patch("builtins.input", side_effect=["n"]):
            with self.assertRaises(RuntimeError):
                show_license_cli(temp_path)

        with temp_path.open(encoding="utf-8") as f:
            data = json.load(f)
        self.assertFalse(data.get("license.accepted"))
        os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()
