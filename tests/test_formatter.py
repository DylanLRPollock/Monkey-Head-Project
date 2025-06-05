import unittest
from src.formatter import format_text


class TestFormatter(unittest.TestCase):
    def test_format_text(self):
        text = "one two three four"
        formatted = format_text(text, line_length=7)
        self.assertEqual(formatted, "one\ntwo\nthree\nfour")


if __name__ == "__main__":
    unittest.main()
