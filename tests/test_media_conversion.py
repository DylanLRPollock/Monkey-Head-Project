# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Media Conversion module (tests)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
from pathlib import Path
import wave
import subprocess
import shutil
import pytest

import importlib.util
from types import ModuleType

if shutil.which("ffmpeg") is None:
    pytest.skip("ffmpeg not installed", allow_module_level=True)

spec = importlib.util.spec_from_file_location(
    "media_conversion",
    str(Path(__file__).resolve().parents[1] / "monkey_head" / "media_conversion.py"),
)
mc: ModuleType = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mc)
convert_audio = mc.convert_audio
convert_video = mc.convert_video
convert_file = mc.convert_file
extract_audio = mc.extract_audio
convert_media = mc.convert_media


def _make_wav(path: Path) -> None:
    with wave.open(str(path), "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(44100)
        f.writeframes(b"\x00\x00" * 44100)


def _make_video(path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=red:s=16x16:d=1",
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


def test_convert_audio(tmp_path: Path) -> None:
    src = tmp_path / "in.wav"
    dst = tmp_path / "out.mp3"
    _make_wav(src)
    convert_audio(str(src), str(dst))
    assert dst.exists() and dst.stat().st_size > 0


def test_convert_video(tmp_path: Path) -> None:
    src = tmp_path / "in.mp4"
    dst = tmp_path / "out.avi"
    _make_video(src)
    convert_video(str(src), str(dst))
    assert dst.exists() and dst.stat().st_size > 0


def test_extract_audio(tmp_path: Path) -> None:
    src = tmp_path / "clip.mp4"
    dst = tmp_path / "clip.aac"
    _make_video(src)
    extract_audio(str(src), str(dst))
    assert dst.exists() and dst.stat().st_size > 0


def test_convert_file(tmp_path: Path) -> None:
    src = tmp_path / "a.txt"
    dst = tmp_path / "b.bin"
    src.write_text("hello")
    convert_file(str(src), str(dst))
    assert dst.read_text() == "hello"


def test_convert_media_audio(tmp_path: Path) -> None:
    src = tmp_path / "snd.wav"
    dst = tmp_path / "snd.mp3"
    _make_wav(src)
    convert_media(str(src), str(dst))
    assert dst.exists() and dst.stat().st_size > 0


def test_convert_media_video(tmp_path: Path) -> None:
    src = tmp_path / "vid.mp4"
    dst = tmp_path / "vid.avi"
    _make_video(src)
    convert_media(str(src), str(dst))
    assert dst.exists() and dst.stat().st_size > 0


def test_convert_media_extract_audio(tmp_path: Path) -> None:
    src = tmp_path / "movie.mp4"
    dst = tmp_path / "movie.mp3"
    _make_video(src)
    convert_media(str(src), str(dst))
    assert dst.exists() and dst.stat().st_size > 0


def test_convert_media_generic(tmp_path: Path) -> None:
    src = tmp_path / "data.bin"
    dst = tmp_path / "copy.bin"
    src.write_text("x")
    convert_media(str(src), str(dst))
    assert dst.read_text() == "x"
