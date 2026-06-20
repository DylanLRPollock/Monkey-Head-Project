"""Tests for media parser adapters layered on the FFmpeg stack."""

from __future__ import annotations

from pathlib import Path

from huey.data.parsers import audio_parser as audio_parser_module
from huey.data.parsers.audio_parser import AudioParser
from huey.data.parsers.video_parser import VideoParser
from huey.media.media_manager import MediaProbeResult
from huey.media.video_pipeline import (
    VideoFramePreview,
    VideoPipeline,
    VideoPipelineResult,
)


def test_audio_parser_prepare_audio_uses_speech_pipeline(tmp_path, monkeypatch) -> None:
    source = tmp_path / "voice.wav"
    source.write_bytes(b"audio")
    prepared = tmp_path / "voice.ready.wav"

    probe = MediaProbeResult(
        path=source,
        format_name="wav",
        duration_seconds=1.5,
        bit_rate=64000,
        size_bytes=5,
        streams=[],
        raw={"format": {"format_name": "wav", "duration": "1.5"}, "streams": []},
    )

    monkeypatch.setattr(audio_parser_module, "probe_media", lambda path: probe)
    monkeypatch.setattr(
        audio_parser_module,
        "validate_media_environment",
        lambda: {"ready": True, "ffmpeg": True, "ffprobe": True},
    )

    def fake_prepare(path: Path, *, output_path: Path | None = None) -> Path:
        assert path == source.resolve()
        assert output_path == prepared.resolve()
        prepared.write_bytes(b"prepared")
        return prepared.resolve()

    monkeypatch.setattr(audio_parser_module, "prepare_for_whisper", fake_prepare)

    result = AudioParser().prepare_audio(source, output_path=prepared)

    assert result.status == "prepared"
    assert result.prepared_path == str(prepared.resolve())
    assert result.format_name == "wav"


def test_video_pipeline_inspect_returns_structured_metadata(tmp_path, monkeypatch) -> None:
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"video")

    monkeypatch.setattr(
        "huey.media.video_pipeline.video_metadata",
        lambda path: {"format": {"duration": "2.0"}, "streams": [{"r_frame_rate": "24/1"}]},
    )
    monkeypatch.setattr("huey.media.video_pipeline.video_duration", lambda path: 2.0)
    monkeypatch.setattr("huey.media.video_pipeline.video_fps", lambda path: 24.0)
    monkeypatch.setattr(
        "huey.media.video_pipeline.validate_media_environment",
        lambda: {"ready": False, "ffmpeg": False, "ffprobe": False},
    )

    result = VideoPipeline().inspect(source)

    assert result.source_path == str(source.resolve())
    assert result.duration_seconds == 2.0
    assert result.fps == 24.0
    assert result.ffmpeg["ready"] is False


def test_video_parser_extract_preview_uses_video_pipeline(tmp_path) -> None:
    source = tmp_path / "clip.mp4"
    preview = tmp_path / "clip.preview.png"

    class FakePipeline:
        def inspect(self, source_path: str | Path) -> VideoPipelineResult:
            return VideoPipelineResult(
                source_path=str(Path(source_path).resolve()),
                duration_seconds=4.0,
                fps=30.0,
                metadata={"format": {"duration": "4.0"}},
                ffmpeg={"ready": True},
            )

        def extract_preview(
            self,
            source_path: str | Path,
            target_path: str | Path,
            *,
            timestamp_seconds: float = 1.0,
        ) -> VideoFramePreview:
            return VideoFramePreview(
                source_path=str(Path(source_path).resolve()),
                preview_path=str(Path(target_path).resolve()),
                timestamp_seconds=timestamp_seconds,
                duration_seconds=4.0,
                fps=30.0,
                metadata={"format": {"duration": "4.0"}},
                ffmpeg={"ready": True},
            )

    parser = VideoParser(FakePipeline())
    result = parser.extract_preview(source, output_path=preview, timestamp_seconds=2.5)

    assert result.status == "preview-extracted"
    assert result.preview_path == str(preview.resolve())
    assert result.duration_seconds == 4.0
