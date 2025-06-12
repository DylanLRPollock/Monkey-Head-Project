# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
from PIL import Image

from monkey_head.convert_png_to_jpeg import convert_png_to_jpeg


def test_convert_png_to_jpeg(tmp_path):
    png_file = tmp_path / "test.png"
    jpeg_file = tmp_path / "out.jpg"

    # create simple red square PNG
    img = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
    img.save(png_file)

    convert_png_to_jpeg(str(png_file), str(jpeg_file))

    assert jpeg_file.exists()
    assert jpeg_file.stat().st_size > 0
