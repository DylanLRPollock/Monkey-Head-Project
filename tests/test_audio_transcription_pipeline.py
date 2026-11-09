"""Tests for the optional audio transcription pipeline."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from huey.audio import transcription_pipeline as pipeline


def test_default_prepared_path_uses_source_stem_and_audio_directory(
    tmp_path, monkeypatch
) -> None:
    source = tmp_path / "recording.flac"
    source.touch()
    monkeypatch.setattr(pipeline, "ensure_subdirectory", lambda *parts: tmp_path)

    assert pipeline._default_prepared_path(source) == tmp_path / "recording.whisper.wav"


def test_mock_transcription_skips_preparation_and_returns_stable_payload(
    tmp_path, monkeypatch
) -> None:
    source = tmp_path / "voice.wav"
    prepared = tmp_path / "voice.whisper.wav"

    def unexpected_prepare(*args, **kwargs):
        pytest.fail(
            "mock transcription without a custom backend must not prepare audio"
        )

    monkeypatch.setattr(pipeline, "prepare_for_whisper", unexpected_prepare)
    result = pipeline.transcribe(source, mock=True)

    assert result == {
        "source_file": str(source.resolve()),
        "prepared_file": str(source.resolve()),
        "transcript": "Mock transcript for voice.wav",
        "segments": [],
        "language": "en",
        "transcription_engine": "mock-transcriber",
        "transcription_model": "small.en",
    }
    assert not prepared.exists()


def test_custom_transcriber_string_skips_preparation_when_requested(tmp_path) -> None:
    source = tmp_path / "voice.wav"
    calls: list[str] = []

    def custom(path: str) -> str:
        calls.append(path)
        return "hello there"

    result = pipeline.transcribe(source, transcriber=custom, prepare_audio=False)

    assert calls == [str(source.resolve())]
    assert result == {
        "transcript": "hello there",
        "transcription_engine": "custom",
        "transcription_model": "small.en",
        "language": "en",
        "source_file": str(source.resolve()),
        "prepared_file": str(source.resolve()),
    }


def test_custom_transcriber_preserves_metadata_and_prepares_audio(
    tmp_path, monkeypatch
) -> None:
    source = tmp_path / "voice.wav"
    prepared = tmp_path / "prepared.wav"
    calls: list[tuple[Path, Path]] = []

    def fake_prepare(path: Path, *, output_path: Path) -> Path:
        calls.append((path, output_path))
        return prepared

    monkeypatch.setattr(
        pipeline, "_default_prepared_path", lambda path: tmp_path / "target.wav"
    )
    monkeypatch.setattr(pipeline, "prepare_for_whisper", fake_prepare)

    def custom(path: str) -> dict[str, object]:
        assert path == str(prepared)
        return {
            "transcript": "custom result",
            "language": "fr",
            "transcription_model": "custom-model",
            "extra": 7,
        }

    result = pipeline.transcribe(
        source,
        transcriber=custom,
        model_name="requested-model",
        language="en",
    )

    assert calls == [(source.resolve(), tmp_path / "target.wav")]
    assert result == {
        "transcript": "custom result",
        "language": "fr",
        "transcription_model": "custom-model",
        "extra": 7,
        "transcription_engine": "custom",
        "source_file": str(source.resolve()),
        "prepared_file": str(prepared),
    }


def test_faster_whisper_backend_collects_segments_and_runtime_metadata(
    tmp_path, monkeypatch
) -> None:
    source = tmp_path / "voice.wav"
    prepared = tmp_path / "prepared.wav"
    model_calls: list[tuple[str, str, str]] = []

    class FakeModel:
        def __init__(self, model_name: str, *, device: str, compute_type: str) -> None:
            model_calls.append((model_name, device, compute_type))

        def transcribe(self, path: str, *, language: str):
            assert path == str(prepared)
            assert language == "en"
            return iter(
                [
                    SimpleNamespace(start=0, end=1.5, text=" hello "),
                    SimpleNamespace(start=1.5, end=2, text=" world "),
                    SimpleNamespace(start=2, end=3, text="   "),
                ]
            ), SimpleNamespace(language="en", duration=3.0)

    monkeypatch.setattr(
        pipeline, "prepare_for_whisper", lambda *args, **kwargs: prepared
    )
    monkeypatch.setattr(
        pipeline, "_default_prepared_path", lambda path: tmp_path / "target.wav"
    )
    monkeypatch.setitem(
        sys.modules,
        "faster_whisper",
        SimpleNamespace(WhisperModel=FakeModel),
    )

    result = pipeline.transcribe(source)

    assert model_calls == [("small.en", "auto", "int8")]
    assert result == {
        "source_file": str(source.resolve()),
        "prepared_file": str(prepared),
        "transcript": "hello world",
        "segments": [
            {"start": 0.0, "end": 1.5, "text": "hello"},
            {"start": 1.5, "end": 2.0, "text": "world"},
            {"start": 2.0, "end": 3.0, "text": ""},
        ],
        "language": "en",
        "duration": 3.0,
        "transcription_engine": "faster-whisper",
        "transcription_model": "small.en",
    }


def test_faster_whisper_backend_uses_requested_language_when_info_omits_it(
    tmp_path, monkeypatch
) -> None:
    class FakeModel:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def transcribe(self, path: str, *, language: str):
            return iter(()), SimpleNamespace()

    monkeypatch.setattr(
        pipeline, "prepare_for_whisper", lambda *args, **kwargs: path
    )
    monkeypatch.setattr(
        pipeline,
        "_default_prepared_path",
        lambda source: tmp_path / "prepared.wav",
    )
    path = tmp_path / "prepared.wav"
    monkeypatch.setitem(
        sys.modules,
        "faster_whisper",
        SimpleNamespace(WhisperModel=FakeModel),
    )

    result = pipeline.transcribe(tmp_path / "voice.wav", language="es")

    assert result["language"] == "es"
    assert result["duration"] is None
    assert result["segments"] == []
    assert result["transcript"] == ""


def test_missing_faster_whisper_reports_install_or_injection_guidance(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setitem(sys.modules, "faster_whisper", None)

    with pytest.raises(RuntimeError, match="pass a custom transcriber or mock=True"):
        pipeline.transcribe(tmp_path / "voice.wav", prepare_audio=False)


def test_batch_transcribe_forwards_backend_options(tmp_path, monkeypatch) -> None:
    calls: list[tuple[Path, dict[str, object]]] = []

    def fake_transcribe(source: str | Path, **kwargs) -> dict[str, object]:
        calls.append((Path(source), kwargs))
        return {"source_file": str(source)}

    monkeypatch.setattr(pipeline, "transcribe", fake_transcribe)
    sources = [tmp_path / "one.wav", tmp_path / "two.wav"]

    results = pipeline.batch_transcribe(
        sources,
        model_name="tiny",
        language="de",
        prepare_audio=False,
        mock=True,
    )

    assert [Path(item["source_file"]) for item in results] == sources
    assert calls == [
        (
            source,
            {
                "transcriber": None,
                "model_name": "tiny",
                "language": "de",
                "prepare_audio": False,
                "mock": True,
            },
        )
        for source in sources
    ]


def test_transcription_metadata_returns_stable_subset() -> None:
    payload = {
        "source_file": "source.wav",
        "prepared_file": "prepared.wav",
        "language": "en",
        "transcription_engine": "faster-whisper",
        "transcription_model": "small.en",
        "duration": 2.5,
        "segments": [{"text": "one"}, {"text": "two"}],
        "transcript": "one two",
        "private": "excluded",
    }

    assert pipeline.transcription_metadata(payload) == {
        "source_file": "source.wav",
        "prepared_file": "prepared.wav",
        "language": "en",
        "transcription_engine": "faster-whisper",
        "transcription_model": "small.en",
        "duration": 2.5,
        "segment_count": 2,
    }
