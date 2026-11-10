"""Offline tests for the public video pipeline operations."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import huey.media.video_pipeline as video_module
from huey.media.media_manifest import MediaProbe
from huey.media.video_pipeline import (
    VideoFramePreview,
    VideoPipeline,
    VideoPipelineResult,
    build_video_preview,
    extract_frames,
    extract_keyframes,
    extract_thumbnail,
    extract_video_frame,
    split_video,
    video_duration,
    video_fps,
    video_metadata,
)


def _source(tmp_path: Path) -> Path:
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"video fixture")
    return source


class ManagerStub:
    def __init__(self):
        self.calls = []
        self.probe_result = MediaProbe(
            path="/tmp/clip.mp4",
            format_name="mp4",
            duration_seconds=4.5,
            bit_rate=64000,
            streams=[{"codec_type": "video"}],
        )

    def probe(self, source):
        self.calls.append(("probe", source))
        return self.probe_result

    def thumbnail(self, source, target, *, overwrite=False):
        self.calls.append(("thumbnail", source, target, overwrite))
        return SimpleNamespace(command=["ffmpeg", "thumbnail"])

    def extract_audio(self, source, target, *, overwrite=False):
        self.calls.append(("extract_audio", source, target, overwrite))
        return SimpleNamespace(command=["ffmpeg", "audio"])

    def extract_frame(self, source, output, *, frame_number, overwrite=False):
        self.calls.append(("extract_frame", source, output, frame_number, overwrite))


def test_result_dataclasses_return_independent_serializable_mappings():
    result = VideoPipelineResult("source.mp4", 2.0, 24.0, {"x": 1}, {"ready": True})
    preview = VideoFramePreview(
        "source.mp4", "preview.jpg", 1.0, 2.0, 24.0, {"x": 1}, {"ready": True}
    )
    result_dict = result.to_dict()
    preview_dict = preview.to_dict()
    result_dict["metadata"]["x"] = 2
    preview_dict["ffmpeg"]["ready"] = False
    assert result.metadata == {"x": 1}
    assert preview.ffmpeg == {"ready": True}
    assert preview_dict["timestamp_seconds"] == 1.0


def test_video_pipeline_extract_preview_and_segment_wrap_functional_helpers(
    tmp_path, monkeypatch
):
    source = _source(tmp_path)
    preview_path = tmp_path / "preview.jpg"
    calls = []
    monkeypatch.setattr(
        video_module,
        "extract_thumbnail",
        lambda *a, **k: calls.append((a, k)) or preview_path,
    )
    monkeypatch.setattr(
        video_module,
        "video_metadata",
        lambda _path: {"format": {"duration": "3"}, "streams": []},
    )
    monkeypatch.setattr(video_module, "video_duration", lambda _path: 3.0)
    monkeypatch.setattr(video_module, "video_fps", lambda _path: 25.0)
    monkeypatch.setattr(
        video_module, "validate_media_environment", lambda: {"ready": True}
    )
    pipeline = VideoPipeline()

    preview = pipeline.extract_preview(source, preview_path, timestamp_seconds=1.25)
    assert preview.preview_path == str(preview_path)
    assert preview.timestamp_seconds == 1.25
    assert calls[0][1] == {"timestamp": 1.25}

    chunks = [tmp_path / "chunks" / "segment-001.mp4"]
    monkeypatch.setattr(video_module, "split_video", lambda *a, **k: chunks)
    segmented = pipeline.segment(
        source, tmp_path / "chunks", chunk_seconds=12, prefix="part"
    )
    assert segmented["segments"] == [str(chunks[0])]
    assert segmented["chunk_seconds"] == 12
    assert segmented["inspection"]["fps"] == 25.0


def test_extract_frames_delegates_fps_and_paths(monkeypatch, tmp_path):
    source = _source(tmp_path)
    output = tmp_path / "frames" / "frame-%03d.png"
    calls = []
    expected = output.parent
    monkeypatch.setattr(
        video_module,
        "_extract_frames",
        lambda *args, **kwargs: calls.append((args, kwargs)) or expected,
    )
    assert extract_frames(source, output, fps=2.5) == expected
    assert calls == [((source, output), {"fps": 2.5})]


def test_extract_keyframes_builds_safe_ffmpeg_argument_list(monkeypatch, tmp_path):
    source = _source(tmp_path)
    target = tmp_path / "keyframes" / "key-%03d.jpg"
    commands = []
    monkeypatch.setattr(video_module, "_run_ffmpeg", commands.append)
    result = extract_keyframes(source, target)
    assert result == target
    assert target.parent.is_dir()
    assert commands == [
        [
            "-i",
            str(source.resolve()),
            "-vf",
            "select='eq(pict_type,I)'",
            "-vsync",
            "vfr",
            str(target),
        ]
    ]


def test_extract_thumbnail_builds_timestamp_command(monkeypatch, tmp_path):
    source = _source(tmp_path)
    target = tmp_path / "thumbs" / "preview.jpg"
    commands = []
    monkeypatch.setattr(video_module, "_run_ffmpeg", commands.append)
    result = extract_thumbnail(source, target, timestamp=2.75)
    assert result == target
    assert target.parent.is_dir()
    assert commands == [
        ["-ss", "2.75", "-i", str(source.resolve()), "-frames:v", "1", str(target)]
    ]


def test_split_video_builds_segments_and_returns_sorted_matches(monkeypatch, tmp_path):
    source = _source(tmp_path)
    output_dir = tmp_path / "segments"
    output_dir.mkdir()
    (output_dir / "part-002.mp4").write_bytes(b"2")
    (output_dir / "part-001.mp4").write_bytes(b"1")
    (output_dir / "other-001.mp4").write_bytes(b"other")
    commands = []
    monkeypatch.setattr(video_module, "_run_ffmpeg", commands.append)
    result = split_video(source, output_dir, chunk_seconds=10, prefix="part")
    assert [path.name for path in result] == ["part-001.mp4", "part-002.mp4"]
    assert commands[0][-2:] == ["10", str(output_dir / "part-%03d.mp4")]
    assert commands[0][:4] == ["-i", str(source.resolve()), "-c", "copy"]


def test_metadata_helpers_probe_format_duration_and_stream_rates(monkeypatch, tmp_path):
    source = _source(tmp_path)
    probes = []

    def probe(path):
        probes.append(path)
        return SimpleNamespace(
            raw={
                "format": {"duration": "4.75"},
                "streams": [
                    {"codec_type": "audio", "r_frame_rate": "1/1"},
                    {"codec_type": "video", "r_frame_rate": "30000/1001"},
                ],
            }
        )

    monkeypatch.setattr(video_module, "probe_media", probe)
    assert video_metadata(source)["format"]["duration"] == "4.75"
    assert video_duration(source) == 4.75
    assert video_fps(source) == pytest.approx(30000 / 1001)
    assert probes == [source, source, source]


@pytest.mark.parametrize(
    ("streams", "expected"),
    [
        ([{"codec_type": "video", "r_frame_rate": "24/0"}], 24.0),
        ([{"codec_type": "video", "r_frame_rate": "7"}], 7.0),
        ([{"codec_type": "audio"}], 0.0),
        ([], 0.0),
    ],
)
def test_video_fps_handles_zero_denominator_integer_and_missing_video(
    monkeypatch, streams, expected
):
    monkeypatch.setattr(
        video_module,
        "probe_media",
        lambda _path: SimpleNamespace(raw={"streams": streams}),
    )
    assert video_fps("clip.mp4") == expected


def test_build_video_preview_records_artifacts_commands_and_manifest(tmp_path):
    source = _source(tmp_path)
    manager = ManagerStub()
    manifest = build_video_preview(source, tmp_path / "output", manager=manager)
    manifest_path = tmp_path / "output" / "clip.video.manifest.json"
    saved = json.loads(manifest_path.read_text())
    assert manifest.operation == "build_video_preview"
    assert manifest.source_path == str(source.resolve())
    assert [artifact.role for artifact in manifest.artifacts] == [
        "thumbnail",
        "extracted_transcription_audio",
    ]
    assert saved["metadata"] == {"preserves_source": True}
    assert saved["commands"] == [["ffmpeg", "thumbnail"], ["ffmpeg", "audio"]]
    assert [call[0] for call in manager.calls] == [
        "probe",
        "thumbnail",
        "extract_audio",
    ]
    assert source.read_bytes() == b"video fixture"


def test_build_video_preview_rejects_missing_source(tmp_path):
    with pytest.raises(FileNotFoundError, match="Video source not found"):
        build_video_preview(
            tmp_path / "missing.mp4", tmp_path / "output", manager=ManagerStub()
        )


def test_build_video_preview_constructs_default_manager(monkeypatch, tmp_path):
    source = _source(tmp_path)
    manager = ManagerStub()
    monkeypatch.setattr(video_module, "FFmpegManager", lambda: manager)
    result = build_video_preview(source, tmp_path / "output")
    assert result.operation == "build_video_preview"
    assert manager.calls[0][0] == "probe"


def test_extract_video_frame_delegates_manager_options_and_resolves_output(
    tmp_path,
):
    source = _source(tmp_path)
    output = tmp_path / "frames" / "frame.png"
    manager = ManagerStub()
    result = extract_video_frame(
        source, output, frame_number=12, manager=manager, overwrite=True
    )
    assert result == output.resolve()
    assert manager.calls == [
        ("extract_frame", source, output, 12, True),
    ]


def test_extract_video_frame_constructs_default_manager(monkeypatch, tmp_path):
    source = _source(tmp_path)
    manager = ManagerStub()
    monkeypatch.setattr(video_module, "FFmpegManager", lambda: manager)
    output = extract_video_frame(source, tmp_path / "frame.png", frame_number=0)
    assert output.name == "frame.png"
    assert manager.calls[0][0] == "extract_frame"
