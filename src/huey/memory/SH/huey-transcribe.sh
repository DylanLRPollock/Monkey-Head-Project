#!/bin/bash
set -e

if [ $# -lt 1 ]; then
    echo "Usage: huey-transcribe.sh <audio-or-video-file> [model] [language]"
    echo
    echo "Examples:"
    echo "  huey-transcribe.sh concert.mkv"
    echo "  huey-transcribe.sh concert.mkv large-v3 en"
    echo "  huey-transcribe.sh concert.mkv medium en"
    echo "  huey-transcribe.sh concert.mkv large-v3 auto"
    exit 1
fi

INPUT="$1"
MODEL="${2:-large-v3}"
LANGUAGE="${3:-en}"

if [ ! -f "$INPUT" ]; then
    echo "Input file not found: $INPUT"
    exit 1
fi

SCRIPT_VENV="$HOME/venvs/FasterWhisper/bin/activate"

if [ ! -f "$SCRIPT_VENV" ]; then
    echo "Missing FasterWhisper venv:"
    echo "$SCRIPT_VENV"
    echo
    echo "Create it with:"
    echo "python3 -m venv ~/venvs/FasterWhisper"
    echo "source ~/venvs/FasterWhisper/bin/activate"
    echo "pip install faster-whisper"
    exit 1
fi

INPUT_ABS="$(realpath "$INPUT")"
INPUT_DIR="$(dirname "$INPUT_ABS")"
BASE="$(basename "$INPUT_ABS")"
NAME="${BASE%.*}"

OUTDIR="$INPUT_DIR/${NAME}_transcript_${MODEL}"
mkdir -p "$OUTDIR"

source "$SCRIPT_VENV"

python - "$INPUT_ABS" "$MODEL" "$LANGUAGE" "$OUTDIR" "$NAME" <<'PY'
import json
import sys
from pathlib import Path
from faster_whisper import WhisperModel

input_file = sys.argv[1]
model_name = sys.argv[2]
language = sys.argv[3]
outdir = Path(sys.argv[4])
name = sys.argv[5]

model = WhisperModel(
    model_name,
    device="cpu",
    compute_type="int8",
    cpu_threads=8,
    num_workers=1,
)

kwargs = {
    "beam_size": 5,
    "vad_filter": True,
    "word_timestamps": False,
}

if language.lower() != "auto":
    kwargs["language"] = language
    kwargs["task"] = "transcribe"

segments, info = model.transcribe(input_file, **kwargs)
segments = list(segments)

safe_model = model_name.replace("/", "_")
txt_path = outdir / f"{name}.{safe_model}.txt"
srt_path = outdir / f"{name}.{safe_model}.srt"
json_path = outdir / f"{name}.{safe_model}.json"

def fmt_srt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h = ms // 3600000
    ms %= 3600000
    m = ms // 60000
    ms %= 60000
    s = ms // 1000
    ms %= 1000
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

with txt_path.open("w", encoding="utf-8") as f:
    f.write(f"File: {input_file}\n")
    f.write(f"Model: {model_name}\n")
    f.write(f"Device: CPU\n")
    f.write(f"Compute type: int8\n")
    f.write(f"Language: {info.language} ({info.language_probability:.2f})\n")
    f.write("\n")
    for seg in segments:
        f.write(seg.text.strip() + "\n")

with srt_path.open("w", encoding="utf-8") as f:
    for i, seg in enumerate(segments, start=1):
        f.write(f"{i}\n")
        f.write(f"{fmt_srt_time(seg.start)} --> {fmt_srt_time(seg.end)}\n")
        f.write(seg.text.strip() + "\n\n")

payload = {
    "file": input_file,
    "model": model_name,
    "device": "cpu",
    "compute_type": "int8",
    "language": info.language,
    "language_probability": info.language_probability,
    "duration": info.duration,
    "segments": [
        {
            "id": i,
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
        }
        for i, seg in enumerate(segments)
    ],
}

with json_path.open("w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2, ensure_ascii=False)

print(f"Detected language: {info.language} ({info.language_probability:.2f})")
print(f"Wrote: {txt_path}")
print(f"Wrote: {srt_path}")
print(f"Wrote: {json_path}")
PY
