from __future__ import annotations

import unittest

from huey.media.silence_parser import parse_silencedetect_text


class SilenceParserTests(unittest.TestCase):
    def test_parse_silencedetect_text(self) -> None:
        text = """
        [silencedetect @ 0x1] silence_start: 1.5
        [silencedetect @ 0x1] silence_end: 3.25 | silence_duration: 1.75
        """

        regions = parse_silencedetect_text(text)

        self.assertEqual(
            regions,
            [{"start_seconds": 1.5, "end_seconds": 3.25, "duration_seconds": 1.75}],
        )


if __name__ == "__main__":
    unittest.main()
