# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Convert Video To Gif module (tests)

import importlib.util
import shutil

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
import subprocess
from pathlib import Path

import pytest

if shutil.which("ffmpeg") is None:
    pytest.skip("ffmpeg not installed", allow_module_level=True)

module_path = Path(__file__).resolve().parents[1] / "hueyos" / "convert_video_to_gif.py"
spec = importlib.util.spec_from_file_location("cvg", module_path)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
convert_video_to_gif = module.convert_video_to_gif


def _make_mp4(path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=green:s=16x16:d=1",
            "-f",
            "lavfi",
            "-i",
            "sine=d=1",
            "-shortest",
            str(path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def test_convert_video_to_gif(tmp_path: Path) -> None:
    src = tmp_path / "clip.mp4"
    dst = tmp_path / "clip.gif"
    _make_mp4(src)
    convert_video_to_gif(str(src), str(dst))
    assert dst.exists() and dst.stat().st_size > 0
