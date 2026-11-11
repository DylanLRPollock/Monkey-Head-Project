"""Exercise memory ingestion copies and FFmpeg audio analysis helpers."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from huey.media import audio_analysis
from huey.memory import ingestion


def test_ingestion_rejects_missing_sources_and_handles_existing_destinations(
    monkeypatch, tmp_path
):
    memory = tmp_path / "memory"
    monkeypatch.setenv("MEMORY_PATH", str(memory))
    with pytest.raises(FileNotFoundError):
        ingestion.ingest_txt(tmp_path / "missing.txt")

    source = tmp_path / "source.txt"
    source.write_text("first")
    target_dir = memory / "INGESTED" / "TXT"
    target_dir.mkdir(parents=True)
    target = target_dir / source.name
    target.mkdir()
    with pytest.raises(FileExistsError, match="not a file"):
        ingestion.ingest_txt(source)

    target.rmdir()
    target.write_text("first")
    assert Path(ingestion.ingest_txt(source)["path"]) == target
    target.write_text("different")
    with pytest.raises(FileExistsError, match="Different file"):
        ingestion.ingest_txt(source)


def test_ingestion_same_path_json_and_media_probe(monkeypatch, tmp_path):
    memory = tmp_path / "memory"
    monkeypatch.setenv("MEMORY_PATH", str(memory))
    text_dir = memory / "INGESTED" / "TXT"
    text_dir.mkdir(parents=True)
    text_path = text_dir / "existing.txt"
    text_path.write_text("line one\nline two")
    assert ingestion.ingest_txt(text_path)["path"] == str(text_path)

    payload = tmp_path / "payload.json"
    payload.write_text('{"healthy": true}')
    assert ingestion.ingest_json(payload, store_copy=False)["content"] == {
        "healthy": True
    }

    audio = tmp_path / "voice.wav"
    video = tmp_path / "clip.mp4"
    audio.write_bytes(b"audio")
    video.write_bytes(b"video")
    calls = []
    monkeypatch.setattr(
        ingestion,
        "probe_media",
        lambda path: (
            calls.append(Path(path)) or SimpleNamespace(raw={"format": "fixture"})
        ),
    )
    assert ingestion.ingest_audio(audio, store_copy=False)["probe"] == {
        "format": "fixture"
    }
    assert ingestion.ingest_video(video, store_copy=False)["probe"] == {
        "format": "fixture"
    }
    assert calls == [audio.resolve(), video.resolve()]


def test_pdf_ingestion_extracts_pages_or_reports_parser_unavailable(
    monkeypatch, tmp_path
):
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"not a real pdf; parser is controlled")
    pypdf = ModuleType("pypdf")
    pypdf.PdfReader = lambda _path: SimpleNamespace(
        pages=[
            SimpleNamespace(extract_text=lambda: " first page "),
            SimpleNamespace(extract_text=lambda: None),
            SimpleNamespace(extract_text=lambda: "second page"),
        ]
    )
    monkeypatch.setitem(sys.modules, "pypdf", pypdf)
    extracted = ingestion.ingest_pdf(pdf, store_copy=False)
    assert extracted["parser"] == "pypdf"
    assert extracted["page_count"] == 3
    assert extracted["content"] == "first page\n\nsecond page"

    monkeypatch.setitem(sys.modules, "pypdf", None)
    unavailable = ingestion.ingest_pdf(pdf, store_copy=False)
    assert unavailable["parser"] == "unavailable"
    assert unavailable["page_count"] == 0
    assert unavailable["content"] == ""


def test_audio_analysis_parses_stream_metadata_and_ffmpeg_results(tmp_path):
    source = tmp_path / "recording.wav"
    source.write_bytes(b"fixture")
    calls = []

    class Manager:
        ffmpeg_bin = "ffmpeg-test"

        def probe(self, path):
            assert path == source.resolve()
            return SimpleNamespace(
                streams=[
                    {"codec_type": "video", "channels": 9},
                    {"codec_type": "audio", "channels": "2", "sample_rate": "48000"},
                ],
                duration_seconds=3.5,
                bit_rate=192000,
            )

        def run(self, command):
            calls.append(command)
            stderr = (
                "mean_volume: -19.5 dB\nmax_volume: -2 dB"
                if len(calls) == 1
                else "silence_start: 1.0\nsilence_end: 1.5 | silence_duration: 0.5"
            )
            return SimpleNamespace(stderr=stderr)

    report = audio_analysis.analyze_audio(source, manager=Manager())
    assert report.duration_seconds == 3.5
    assert report.channels == 2
    assert report.sample_rate_hz == 48000
    assert report.mean_volume_db == -19.5
    assert report.max_volume_db == -2
    assert report.silence_regions == [
        {"start_seconds": 1.0, "end_seconds": 1.5, "duration_seconds": 0.5}
    ]
    assert len(calls) == 2
    assert "volumedetect" in calls[0]
    assert "silencedetect=noise=-35dB:d=0.5" in calls[1]
    assert report.to_json_dict()["path"] == str(source.resolve())


def test_audio_analysis_missing_metadata_and_convenience_wrappers(
    monkeypatch, tmp_path
):
    source = tmp_path / "silent.wav"
    source.touch()
    report = audio_analysis.AudioAnalysis(
        path=str(source),
        duration_seconds=None,
        bit_rate=None,
        channels=None,
        sample_rate_hz=None,
    )
    monkeypatch.setattr(audio_analysis, "analyze_audio", lambda _source: report)
    assert audio_analysis.duration(source) == 0.0
    assert audio_analysis.bitrate(source) == 0
    assert audio_analysis.channels(source) == 0
    assert audio_analysis.sample_rate(source) == 0
    assert audio_analysis.peak_level(source) == 0.0
    assert audio_analysis.rms_level(source) == 0.0
    assert audio_analysis.silence_map(source) == []
    assert audio_analysis._optional_int("bad") is None
    assert audio_analysis._optional_int(None) is None
    assert audio_analysis._optional_int("44100") == 44100
    assert (
        audio_analysis._match_float(audio_analysis.MEAN_VOLUME_RE, "no levels") is None
    )
    monkeypatch.undo()
    with pytest.raises(FileNotFoundError, match="Audio source not found"):
        audio_analysis.analyze_audio(tmp_path / "absent.wav")
