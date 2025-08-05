# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
import unittest
from monkey_head.huey_core_data import generate_core_data


class TestHuey(unittest.TestCase):
    def test_generate_core_data(self):
        data = {"a": 1, "b": 2}
        result = generate_core_data(data)
        self.assertTrue(result["processed"])
        self.assertEqual(result["input_length"], 2)
        self.assertEqual(result["details"], data)

    def test_generate_core_data_invalid_input(self):
        with self.assertRaises(ValueError):
            generate_core_data(123)


if __name__ == "__main__":
    unittest.main()
