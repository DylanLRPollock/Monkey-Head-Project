# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Main module (tests)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
# tests/test_main.py

import unittest
from unittest.mock import patch
from pathlib import Path

_missing_dep = ""
try:
    from huey.main import main
except ModuleNotFoundError as e:
    main = None
    _missing_dep = e.name

# Determine if the config file exists. Tests requiring the YAML
# configuration should be skipped when it is absent.
_config_missing = not (Path(__file__).resolve().parents[1] / "config.yaml").is_file()


class TestMain(unittest.TestCase):
    @unittest.skipIf(main is None, "Required dependency missing: %s" % _missing_dep)
    @unittest.skipIf(_config_missing, "config.yaml not found")
    def test_main_runs(self):
        # Test that main() runs without errors and prints the expected sum
        try:
            with patch("builtins.print") as mock_print:
                main()
            printed_output = " ".join(
                str(arg) for call in mock_print.call_args_list for arg in call.args
            )
            self.assertIn("The sum of", printed_output)
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"The main function raised an exception: {e}")


if __name__ == "__main__":
    unittest.main()
