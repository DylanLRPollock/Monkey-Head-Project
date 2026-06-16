from pathlib import Path

from faster_whisper import WhisperModel

INPUT_FILE = Path.home() / "alan_watts.wav"
MODEL_NAME = "medium.en"

model = WhisperModel(
    MODEL_NAME,
    device="cpu",
    compute_type="int8",
    cpu_threads=4,
)

segments, info = model.transcribe(
    str(INPUT_FILE),
    language="en",
    beam_size=5,
    word_timestamps=False,
    condition_on_previous_text=False,
)

segments = list(segments)

txt_path = Path.home() / f"alan_watts_{MODEL_NAME}.txt"
srt_path = Path.home() / f"alan_watts_{MODEL_NAME}.srt"

with txt_path.open("w", encoding="utf-8") as txt:
    txt.write(
        f"Detected language: {info.language} (probability={info.language_probability:.4f})\n\n"
    )
    for seg in segments:
        txt.write(f"[{seg.start:.2f} -> {seg.end:.2f}] {seg.text.strip()}\n")


def srt_timestamp(seconds: float) -> str:
    total_ms = int(round(seconds * 1000))
    hours = total_ms // 3600000
    total_ms %= 3600000
    minutes = total_ms // 60000
    total_ms %= 60000
    secs = total_ms // 1000
    ms = total_ms % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


with srt_path.open("w", encoding="utf-8") as srt:
    for i, seg in enumerate(segments, start=1):
        srt.write(f"{i}\n")
        srt.write(f"{srt_timestamp(seg.start)} --> {srt_timestamp(seg.end)}\n")
        srt.write(seg.text.strip() + "\n\n")

print("Done.")
print(f"TXT: {txt_path}")
print(f"SRT: {srt_path}")
print(f"Language: {info.language} (probability={info.language_probability:.4f})")
print(f"Segments: {len(segments)}")
