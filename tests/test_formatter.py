# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
import unittest
from src.formatter import format_text


class TestFormatter(unittest.TestCase):
    def test_format_text(self):
        text = "one two three four"
        formatted = format_text(text, line_length=7)
        self.assertEqual(formatted, "one\ntwo\nthree\nfour")


if __name__ == "__main__":
    unittest.main()
