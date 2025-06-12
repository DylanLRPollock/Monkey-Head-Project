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

from monkey_head.media_conversion import convert_audio, convert_video, convert_file


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


def test_convert_file(tmp_path: Path) -> None:
    src = tmp_path / "a.txt"
    dst = tmp_path / "b.bin"
    src.write_text("hello")
    convert_file(str(src), str(dst))
    assert dst.read_text() == "hello"
