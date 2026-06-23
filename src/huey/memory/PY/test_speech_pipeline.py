from __future__ import annotations

from pathlib import Path

import pytest

from huey.media.media_manager import CommandResult
from huey.media.speech_pipeline import prepare_audio_for_transcription


class FakeAudioManager:
    def convert_audio(self, source, output, **kwargs):
        Path(output).write_bytes(b"converted")
        return CommandResult(0, "", "", ["ffmpeg", "convert"], Path(output))

    def normalize_audio(self, source, output, **kwargs):
        Path(output).write_bytes(b"normalized")
        return CommandResult(0, "", "", ["ffmpeg", "normalize"], Path(output))


def test_prepare_audio_manifest_with_fake_manager(tmp_path: Path) -> None:
    source = tmp_path / "fixture.mp3"
    output = tmp_path / "fixture.wav"
    source.write_bytes(b"source")
    manifest = prepare_audio_for_transcription(
        source, output, manager=FakeAudioManager()
    )
    assert output.read_bytes() == b"normalized"
    assert manifest.to_json_dict()["source_path"].endswith("fixture.mp3")
    assert len(manifest.commands) == 2


def test_prepare_audio_does_not_overwrite_by_default(tmp_path: Path) -> None:
    source = tmp_path / "fixture.mp3"
    output = tmp_path / "fixture.wav"
    source.write_bytes(b"source")
    output.write_bytes(b"existing")
    with pytest.raises(FileExistsError):
        prepare_audio_for_transcription(source, output, manager=FakeAudioManager())
