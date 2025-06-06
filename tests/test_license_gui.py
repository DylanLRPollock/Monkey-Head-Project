import json
import os
import unittest
from pathlib import Path

from src.license_gui import accept_license


class TestLicenseGui(unittest.TestCase):
    def test_accept_license_updates_config(self):
        temp_path = Path("/tmp/test_config.json")
        data = {"license.accepted": False}
        with temp_path.open("w", encoding="utf-8") as f:
            json.dump(data, f)

        accept_license(temp_path)

        with temp_path.open(encoding="utf-8") as f:
            updated = json.load(f)

        self.assertTrue(updated.get("license.accepted"))
        os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()
