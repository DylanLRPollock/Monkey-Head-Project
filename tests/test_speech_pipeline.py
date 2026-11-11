from __future__ import annotations

from pathlib import Path

import pytest

from huey.media.media_manager import CommandResult
from huey.media.media_manifest import MediaProbe
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


def test_audio_helpers_forward_options_and_create_denoise_parent(tmp_path, monkeypatch):
    from huey.media import speech_pipeline as module

    source = tmp_path / "source.wav"
    source.write_bytes(b"audio")
    calls = []
    monkeypatch.setattr(module, "_normalize_audio", lambda src, dst: Path(dst))
    monkeypatch.setattr(
        module,
        "_resample_audio",
        lambda src, dst, **kwargs: calls.append((Path(src), Path(dst), kwargs)) or Path(dst),
    )
    monkeypatch.setattr(
        module,
        "_remove_silence",
        lambda src, dst, **kwargs: calls.append((Path(src), Path(dst), kwargs)) or Path(dst),
    )
    ffmpeg = []
    monkeypatch.setattr(module, "_run_ffmpeg", lambda args: ffmpeg.append(args))

    assert module.normalize_volume(source, tmp_path / "normalized.wav").name == "normalized.wav"
    assert module.convert_to_mono(source, tmp_path / "mono.wav").name == "mono.wav"
    assert module.convert_to_16khz(source, tmp_path / "16k.wav").name == "16k.wav"
    assert module.remove_silence(source, tmp_path / "trim.wav", threshold="-35dB", min_silence_duration=0.8)
    denoised = module.denoise_audio(
        source, tmp_path / "nested" / "denoised.wav", noise_reduction_filter="afftdn"
    )
    assert denoised.parent.is_dir()
    assert ffmpeg == [["-i", str(source), "-af", "afftdn", str(denoised)]]
    assert calls[0][2] == {"channels": 1, "sample_rate": 44100}
    assert calls[1][2] == {"channels": 1, "sample_rate": 16000}
    assert calls[2][2] == {"threshold": "-35dB", "min_silence_duration": 0.8}


def test_generate_ready_file_uses_default_or_explicit_output_and_order(tmp_path, monkeypatch):
    from huey.media import speech_pipeline as module

    source = tmp_path / "voice.mp3"
    source.write_bytes(b"audio")
    paths = {suffix: tmp_path / f"voice.{suffix}.wav" for suffix in ("normalized", "nosilence", "mono", "ready")}
    monkeypatch.setattr(module, "_default_output_path", lambda _src, suffix: paths[suffix])
    calls = []
    for name in ("normalize_volume", "remove_silence", "convert_to_mono", "convert_to_16khz"):
        monkeypatch.setattr(module, name, lambda src, dst, _name=name: calls.append((_name, Path(src), Path(dst))))

    assert module.generate_transcription_ready_file(source) == paths["ready"]
    assert [name for name, _src, _dst in calls] == ["normalize_volume", "remove_silence", "convert_to_mono", "convert_to_16khz"]
    explicit = tmp_path / "explicit.wav"
    assert module.prepare_for_whisper(source, output_path=explicit) == explicit
    assert calls[-1][2] == explicit


def test_audio_preparation_rejects_existing_output_unless_overwrite(tmp_path):
    source = tmp_path / "source.wav"
    output = tmp_path / "output.wav"
    source.write_bytes(b"audio")
    output.write_bytes(b"existing")
    with pytest.raises(FileExistsError, match="Output already exists"):
        prepare_audio_for_transcription(source, output, manager=object())


def test_audio_preparation_without_probe_cleans_intermediate_on_error(tmp_path):
    source = tmp_path / "source.wav"
    output = tmp_path / "output.wav"
    source.write_bytes(b"audio")

    class FailingManager:
        def convert_audio(self, _source, intermediate, **_kwargs):
            Path(intermediate).write_bytes(b"converted")
            return object()

        def normalize_audio(self, *_args, **_kwargs):
            raise RuntimeError("normalize failed")

    with pytest.raises(RuntimeError, match="normalize failed"):
        prepare_audio_for_transcription(source, output, manager=FailingManager())
    assert not output.with_name("output.converted.wav").exists()


def test_audio_preparation_supports_overwrite_and_missing_command_metadata(tmp_path):
    source = tmp_path / "source.wav"
    output = tmp_path / "output.wav"
    source.write_bytes(b"audio")
    output.write_bytes(b"old")

    class ManagerWithoutOptionalMethods:
        def convert_audio(self, _source, intermediate, **_kwargs):
            Path(intermediate).write_bytes(b"converted")
            return object()

        def normalize_audio(self, _intermediate, target, **_kwargs):
            Path(target).write_bytes(b"normalized")
            return object()

    manifest = prepare_audio_for_transcription(
        source, output, manager=ManagerWithoutOptionalMethods(), overwrite=True
    )
    assert manifest.probe is None
    assert manifest.commands == [[], []]
    assert output.read_bytes() == b"normalized"
    assert not output.with_name("output.converted.wav").exists()
