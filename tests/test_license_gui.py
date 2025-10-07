# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.08.2025
# ==================================================
import json
import os
import unittest
from pathlib import Path

from monkey_head.license_gui import accept_license


class TestLicenseGui(unittest.TestCase):
    def test_accept_license_updates_config(self):
        temp_path = Path("/tmp/test_config.json")
        data = {"license.accepted": False}
        with temp_path.open("w", encoding="utf-8") as f:
            json.dump(data, f)

        accept_license(temp_path, "dummy-hash")

        with temp_path.open(encoding="utf-8") as f:
            updated = json.load(f)

        self.assertTrue(updated.get("license.accepted"))
        self.assertIn("license.accepted_at", updated)
        self.assertEqual(updated.get("license.hash"), "dummy-hash")
        os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()
