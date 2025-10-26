# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Formatter module (tests)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.08.2025
# ==================================================
import unittest

from monkey_head.formatter import format_text


class TestFormatter(unittest.TestCase):
    def test_format_text(self):
        text = "one two three four"
        formatted = format_text(text, line_length=7)
        self.assertEqual(formatted, "one\ntwo\nthree\nfour")


def test_format_text_line_lengths():
    """Validate that no line exceeds the specified length."""
    text = "one two three four five six seven eight"
    for length in [5, 10, 15]:
        formatted = format_text(text, line_length=length)
        for line in formatted.splitlines():
            assert len(line) <= length
        assert "".join(formatted.split()) == text.replace(" ", "")


if __name__ == "__main__":
    unittest.main()
