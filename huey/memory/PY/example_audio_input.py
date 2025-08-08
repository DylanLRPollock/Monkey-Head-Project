# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
"""Simple demonstration of reading audio data from a WAV file."""

from __future__ import annotations

import argparse
import wave
from pathlib import Path


def load_audio(path: str) -> tuple[int, bytes]:
    """Return sample rate and raw frames from ``path``.

    Parameters
    ----------
    path : str
        Path to a WAV file.

    Returns
    -------
    tuple[int, bytes]
        The sample rate and audio data.
    """

    with wave.open(path, "rb") as wav:
        rate = wav.getframerate()
        frames = wav.readframes(wav.getnframes())
    return rate, frames


def main() -> None:
    parser = argparse.ArgumentParser(description="Read a WAV file")
    parser.add_argument("file", type=str, help="Path to WAV file")
    args = parser.parse_args()
    rate, frames = load_audio(args.file)
    duration = len(frames) / (rate * 2)  # assume 16bit mono
    print(f"Loaded {args.file}: {duration:.2f}s @ {rate}Hz")


if __name__ == "__main__":  # pragma: no cover - example script
    main()

