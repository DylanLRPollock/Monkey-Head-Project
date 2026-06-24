from __future__ import annotations

from pathlib import Path

from huey.media.media_manifest import MediaProbe
from huey.media.media_manager import CommandResult
from huey.media.speech_pipeline import prepare_audio_for_transcription


class FakeAudioManager:
    def probe(self, source):
        return MediaProbe(
            path=str(Path(source)),
            format_name="mp3",
            duration_seconds=2.5,
            bit_rate=128000,
            streams=[{"codec_type": "audio"}],
        )

    def convert_audio(self, source, output, **kwargs):
        Path(output).write_bytes(b"converted")
        return CommandResult(0, "", "", ["ffmpeg", "convert"], Path(output))

    def normalize_audio(self, source, output, **kwargs):
        Path(output).write_bytes(b"normalized")
        return CommandResult(0, "", "", ["ffmpeg", "normalize"], Path(output))


def test_prepare_audio_manifest_includes_pipeline_metadata(tmp_path: Path) -> None:
    source = tmp_path / "fixture.mp3"
    output = tmp_path / "fixture.prepared.wav"
    source.write_bytes(b"fixture")

    manifest = prepare_audio_for_transcription(
        source,
        output,
        manager=FakeAudioManager(),
    )

    pipeline = manifest.metadata["pipeline"]
    assert manifest.metadata["preserves_source"] is True
    assert pipeline["boundary"] == "Huey Brain V1 fixture-first audio ingress"
    assert pipeline["input"]["canonical_v1_input"] == "controlled MP3 fixture"
    assert pipeline["input"]["fixture_alignment"] == "canonical"
    assert pipeline["output"]["path"] == str(output)
    assert pipeline["output"]["sample_rate_hz"] == 16000
    assert [step["id"] for step in pipeline["processing"]["steps"]] == [
        "probe_source_media",
        "convert_to_mono_16khz_wav",
        "normalize_loudness",
    ]
    assert [tool["name"] for tool in pipeline["tools"]] == ["ffprobe", "ffmpeg"]
