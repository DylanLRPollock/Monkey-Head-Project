# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Convert Mkv To Mp4 module (tests)

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

# dynamically load the module to avoid import issues
module_path = (
    Path(__file__).resolve().parents[1] / "hueyos" / "convert_mkv_to_mp4.py"
)
spec = importlib.util.spec_from_file_location("c", module_path)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
convert_mkv_to_mp4 = module.convert_mkv_to_mp4


def _make_mkv(path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=16x16:d=1",
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


def test_convert_mkv_to_mp4(tmp_path: Path) -> None:
    src = tmp_path / "clip.mkv"
    dst = tmp_path / "clip.mp4"
    _make_mkv(src)
    convert_mkv_to_mp4(str(src), str(dst))
    assert dst.exists() and dst.stat().st_size > 0
