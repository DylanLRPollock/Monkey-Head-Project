# tests/test_main.py

import unittest
from unittest.mock import patch

_missing_dep = ""
try:
    from huey.main import main
except ModuleNotFoundError as e:
    main = None
    _missing_dep = e.name


class TestMain(unittest.TestCase):
    @unittest.skipIf(main is None, "Required dependency missing: %s" % _missing_dep)
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
