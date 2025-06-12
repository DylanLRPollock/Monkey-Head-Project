# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
# tests/test_utils.py

import os
from pathlib import Path
import unittest

from PIL import Image

from huey.utils import (
    calculate_sum,
    validate_input,
    convert_jpeg_to_png,
    convert_image,
    convert_images_in_directory,
)
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

    def test_convert_image(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            img = Image.new("RGB", (10, 10), color="blue")
            src = tmp_path / "img.png"
            img.save(src, "PNG")

            out_jpeg = convert_image(str(src), "JPEG")
            assert Path(out_jpeg).suffix in {".jpg", ".jpeg"}
            assert Path(out_jpeg).is_file()

            custom_out = tmp_path / "result.jpg"
            out_custom = convert_image(str(src), "JPEG", str(custom_out), quality=90)
            assert out_custom == str(custom_out)
            assert custom_out.is_file()

    def test_convert_images_in_directory(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            for i in range(3):
                Image.new("RGB", (10, 10), color="green").save(
                    tmp_path / f"img_{i}.png", "PNG"
                )

            out_dir = tmp_path / "out"
            results = convert_images_in_directory(str(tmp_path), "JPEG", str(out_dir))

            assert len(results) == 3
            for path in results:
                assert Path(path).suffix in {".jpg", ".jpeg"}
                assert Path(path).is_file()


if __name__ == "__main__":
    unittest.main()
