# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
# tests/test_utils.py

import os
from pathlib import Path
import unittest

from PIL import Image

from huey.utils import calculate_sum, validate_input, convert_jpeg_to_png
from huey.exceptions import InvalidInputError


class TestUtils(unittest.TestCase):
    def test_calculate_sum(self):
        self.assertEqual(calculate_sum(2, 3), 5)
        self.assertEqual(calculate_sum(-1, 1), 0)

    def test_validate_input(self):
        self.assertTrue(validate_input(5, int))
        with self.assertRaises(InvalidInputError):
            validate_input("five", int)

    def test_convert_jpeg_to_png(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            img = Image.new("RGB", (10, 10), color="red")
            jpeg_path = tmp_path / "img.jpg"
            img.save(jpeg_path, "JPEG")

            png_path = convert_jpeg_to_png(str(jpeg_path))
            assert os.path.exists(png_path)
            assert Path(png_path).suffix == ".png"

            custom_out = tmp_path / "out" / "out.png"
            custom_out.parent.mkdir()
            result_path = convert_jpeg_to_png(str(jpeg_path), str(custom_out))
            assert result_path == str(custom_out)
            assert custom_out.is_file()


if __name__ == "__main__":
    unittest.main()
