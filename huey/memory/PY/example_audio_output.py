# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Example Audio Output module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
"""Generate a short sine wave and save it as a WAV file."""

from __future__ import annotations

import argparse
import math
import wave
from array import array


def generate_tone(filename: str, duration: float = 1.0, freq: int = 440) -> None:
    """Create a mono WAV file containing a sine wave."""

    rate = 44100
    amp = 32767
    frames = array("h")
    total_samples = int(duration * rate)
    for i in range(total_samples):
        sample = int(amp * math.sin(2 * math.pi * freq * i / rate))
        frames.append(sample)

    with wave.open(filename, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(frames.tobytes())


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate tone WAV file")
    parser.add_argument("file", type=str, nargs="?", default="tone.wav")
    parser.add_argument("--freq", type=int, default=440)
    parser.add_argument("--duration", type=float, default=1.0)
    args = parser.parse_args()
    generate_tone(args.file, duration=args.duration, freq=args.freq)
    print(f"Saved {args.file}")


if __name__ == "__main__":  # pragma: no cover - example script
    main()
