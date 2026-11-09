"""Dependency-free tests for media-conversion routing and wrappers."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from huey.media import media_conversion as conversion


@pytest.mark.parametrize(
    ("source_extension", "target_extension", "expected"),
    [
        (".mp4", ".mp3", "extract_audio"),
        (".wav", ".mp3", "convert_audio"),
        (".mkv", ".gif", "convert_video_to_gif"),
        (".mp4", ".avi", "convert_video"),
        (".png", ".jpg", "convert_file"),
        (".bin", ".mp3", "convert_file"),
        (".png", ".bin", "convert_file"),
    ],
)
def test_convert_media_dispatches_by_source_and_target_extension(
    tmp_path, monkeypatch, source_extension, target_extension, expected
) -> None:
    source = tmp_path / f"source{source_extension}"
    target = tmp_path / "nested" / f"target{target_extension}"
    source.touch()
    handler = Mock(return_value=target.resolve())
    monkeypatch.setattr(conversion, expected, handler)

    result = conversion.convert_media(source, target)

    assert result == target.resolve()
    handler.assert_called_once()
    assert handler.call_args.args[:2] == (source.resolve(), target)
    if expected == "convert_audio":
        assert handler.call_args.kwargs == {"bitrate": "192k"}
    elif expected == "convert_video":
        assert handler.call_args.kwargs == {"codec": "libx264"}
    else:
        assert handler.call_args.kwargs == {}


def test_conversion_wrappers_validate_source_and_forward_options(
    tmp_path, monkeypatch
) -> None:
    source = tmp_path / "source.wav"
    target = tmp_path / "target.mp3"
    source.touch()
    audio_result = tmp_path / "audio-result.mp3"
    video_result = tmp_path / "video-result.mp4"
    extract_result = tmp_path / "extract-result.wav"
    audio = Mock(return_value=audio_result)
    video = Mock(return_value=video_result)
    extract = Mock(return_value=extract_result)
    monkeypatch.setattr(conversion, "_convert_audio", audio)
    monkeypatch.setattr(conversion, "_transcode_video", video)
    monkeypatch.setattr(conversion, "_extract_audio", extract)

    converted_audio = conversion.convert_audio(source, target, bitrate="320k")
    assert converted_audio == audio_result
    assert audio.call_args.args == (source.resolve(), target)
    assert audio.call_args.kwargs == {"bitrate": "320k"}

    converted_video = conversion.convert_video(source, target, codec="hevc")
    assert converted_video == video_result
    assert video.call_args.args == (source.resolve(), target)
    assert video.call_args.kwargs == {"video_codec": "hevc"}

    extracted_audio = conversion.extract_audio(source, target)
    assert extracted_audio == extract_result
    assert extract.call_args.args == (source.resolve(), target)
    assert extract.call_args.kwargs == {"codec": "libmp3lame"}


@pytest.mark.parametrize(
    ("target_name", "expected_codec"),
    [("target.mp3", "libmp3lame"), ("target.wav", None), ("target.MP3", "libmp3lame")],
)
def test_extract_audio_selects_codec_from_target_extension(
    tmp_path, monkeypatch, target_name, expected_codec
) -> None:
    source = tmp_path / "video.mp4"
    target = tmp_path / target_name
    source.touch()
    extract = Mock(return_value=target)
    monkeypatch.setattr(conversion, "_extract_audio", extract)

    result = conversion.extract_audio(source, target)
    assert result == target
    assert extract.call_args.kwargs == {"codec": expected_codec}


def test_convert_file_creates_parent_and_copies_bytes(tmp_path) -> None:
    source = tmp_path / "source.bin"
    target = tmp_path / "new" / "nested" / "copy.bin"
    source.write_bytes(b"fixture-bytes")

    result = conversion.convert_file(source, target)

    assert result == target.resolve()
    assert target.read_bytes() == b"fixture-bytes"


def test_conversion_wrappers_reject_missing_source(tmp_path) -> None:
    missing = tmp_path / "missing.wav"

    with pytest.raises(FileNotFoundError):
        conversion.convert_file(missing, tmp_path / "target.bin")

    with pytest.raises(FileNotFoundError):
        conversion.convert_audio(missing, tmp_path / "target.mp3")

    with pytest.raises(FileNotFoundError):
        conversion.convert_video(missing, tmp_path / "target.mp4")

    with pytest.raises(FileNotFoundError):
        conversion.extract_audio(missing, tmp_path / "target.wav")
