#!/bin/bash
set -e

if [ $# -lt 1 ]; then
    echo "Usage: huey-transcribe-chunked.sh <audio-or-video-file> [model] [language] [chunk_seconds]"
    echo
    echo "Examples:"
    echo "  huey-transcribe-chunked.sh lecture.mp3"
    echo "  huey-transcribe-chunked.sh lecture.mp3 large-v3 en 600"
    echo "  huey-transcribe-chunked.sh lecture.mp3 medium en 900"
    exit 1
fi

INPUT="$1"
MODEL="${2:-large-v3}"
LANGUAGE="${3:-en}"
CHUNK_SECONDS="${4:-600}"

if [ ! -f "$INPUT" ]; then
    echo "Input file not found: $INPUT"
    exit 1
fi

VENV="$HOME/venvs/FasterWhisper/bin/activate"

if [ ! -f "$VENV" ]; then
    echo "Missing FasterWhisper venv:"
    echo "$VENV"
    exit 1
fi

INPUT_ABS="$(realpath "$INPUT")"
INPUT_DIR="$(dirname "$INPUT_ABS")"
BASE="$(basename "$INPUT_ABS")"
NAME="${BASE%.*}"
SAFE_MODEL="${MODEL//\//_}"

OUTDIR="$INPUT_DIR/${NAME}_transcript_${SAFE_MODEL}_chunked"
CHUNKDIR="$OUTDIR/chunks"

mkdir -p "$OUTDIR" "$CHUNKDIR"

echo "============================================================"
echo " HueyOS chunked transcription"
echo "============================================================"
echo "Input:          $INPUT_ABS"
echo "Model:          $MODEL"
echo "Language:       $LANGUAGE"
echo "Chunk seconds:  $CHUNK_SECONDS"
echo "Output folder:  $OUTDIR"
echo "Device:         CPU"
echo "Compute:        int8"
echo "============================================================"

DURATION="$(ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$INPUT_ABS")"
echo "Detected duration: ${DURATION}s"

echo
echo "[1/4] Creating audio chunks..."
rm -f "$CHUNKDIR"/chunk_*.wav

ffmpeg -hide_banner -y \
    -i "$INPUT_ABS" \
    -vn \
    -ac 1 \
    -ar 16000 \
    -c:a pcm_s16le \
    -f segment \
    -segment_time "$CHUNK_SECONDS" \
    -reset_timestamps 1 \
    "$CHUNKDIR/chunk_%05d.wav"

echo
echo "[2/4] Chunks created:"
ls -lh "$CHUNKDIR"/chunk_*.wav

echo
echo "[3/4] Starting faster-whisper..."
source "$VENV"

python - "$INPUT_ABS" "$MODEL" "$LANGUAGE" "$OUTDIR" "$CHUNKDIR" "$NAME" "$CHUNK_SECONDS" <<'PY'
import json
import subprocess
import sys
import time
from pathlib import Path
from faster_whisper import WhisperModel

input_file = sys.argv[1]
model_name = sys.argv[2]
language = sys.argv[3]
outdir = Path(sys.argv[4])
chunkdir = Path(sys.argv[5])
name = sys.argv[6]
chunk_seconds = float(sys.argv[7])

safe_model = model_name.replace("/", "_")

txt_path = outdir / f"{name}.{safe_model}.chunked.txt"
srt_path = outdir / f"{name}.{safe_model}.chunked.srt"
json_path = outdir / f"{name}.{safe_model}.chunked.json"
log_path = outdir / f"{name}.{safe_model}.chunked.log"

chunks = sorted(chunkdir.glob("chunk_*.wav"))

if not chunks:
    raise SystemExit("No chunks found.")

def probe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=nk=1:nw=1",
            str(path),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return float(result.stdout.strip())

def fmt_srt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h = ms // 3600000
    ms %= 3600000
    m = ms // 60000
    ms %= 60000
    s = ms // 1000
    ms %= 1000
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

print("Loading model. This may take a while on first run/download...")
start_time = time.time()

model = WhisperModel(
    model_name,
    device="cpu",
    compute_type="int8",
    cpu_threads=8,
    num_workers=1,
)

print(f"Model loaded in {time.time() - start_time:.1f}s")
print(f"Total chunks: {len(chunks)}")

all_segments = []
srt_index = 1
offset = 0.0

with txt_path.open("w", encoding="utf-8") as txt, \
     srt_path.open("w", encoding="utf-8") as srt, \
     log_path.open("w", encoding="utf-8") as log:

    txt.write(f"File: {input_file}\n")
    txt.write(f"Model: {model_name}\n")
    txt.write("Device: CPU\n")
    txt.write("Compute type: int8\n")
    txt.write(f"Language request: {language}\n")
    txt.write(f"Chunks: {len(chunks)}\n\n")

    for idx, chunk in enumerate(chunks, start=1):
        chunk_duration = probe_duration(chunk)
        chunk_start = offset
        chunk_end = offset + chunk_duration

        msg = (
            f"[chunk {idx}/{len(chunks)}] "
            f"{chunk.name} | offset={chunk_start:.2f}s | duration={chunk_duration:.2f}s"
        )
        print(msg, flush=True)
        log.write(msg + "\n")
        log.flush()

        kwargs = {
            "beam_size": 5,
            "vad_filter": True,
            "word_timestamps": False,
        }

        if language.lower() != "auto":
            kwargs["language"] = language
            kwargs["task"] = "transcribe"

        chunk_transcribe_start = time.time()
        segments, info = model.transcribe(str(chunk), **kwargs)

        segment_count = 0

        for seg in segments:
            abs_start = chunk_start + seg.start
            abs_end = chunk_start + seg.end
            text = seg.text.strip()

            if not text:
                continue

            segment_count += 1

            all_segments.append({
                "chunk": idx,
                "start": abs_start,
                "end": abs_end,
                "text": text,
            })

            txt.write(text + "\n")

            srt.write(f"{srt_index}\n")
            srt.write(f"{fmt_srt_time(abs_start)} --> {fmt_srt_time(abs_end)}\n")
            srt.write(text + "\n\n")
            srt_index += 1

            print(f"  {fmt_srt_time(abs_start)} --> {fmt_srt_time(abs_end)}  {text[:90]}", flush=True)

        elapsed = time.time() - chunk_transcribe_start
        done_msg = (
            f"[chunk {idx}/{len(chunks)} done] "
            f"segments={segment_count} | elapsed={elapsed:.1f}s | detected={info.language}"
        )
        print(done_msg, flush=True)
        log.write(done_msg + "\n")
        log.flush()

        offset += chunk_duration

payload = {
    "file": input_file,
    "model": model_name,
    "device": "cpu",
    "compute_type": "int8",
    "language_request": language,
    "chunk_seconds": chunk_seconds,
    "chunks": len(chunks),
    "segments": [
        {
            "id": i,
            "chunk": seg["chunk"],
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"],
        }
        for i, seg in enumerate(all_segments, start=1)
    ],
}

with json_path.open("w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2, ensure_ascii=False)

print()
print("============================================================")
print("Transcription complete.")
print(f"Wrote: {txt_path}")
print(f"Wrote: {srt_path}")
print(f"Wrote: {json_path}")
print(f"Wrote: {log_path}")
print("============================================================")
PY

echo
echo "[4/4] Done."
