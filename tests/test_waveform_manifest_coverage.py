"""Cover waveform and spectrogram manifest generation."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from huey.media.waveform_manifest import generate_waveform_manifest


def test_generation_writes_manifest_and_passes_overwrite_flag(tmp_path: Path):
    source = tmp_path / "sample.wav"
    source.write_bytes(b"audio")
    output_dir = tmp_path / "previews"
    calls = []

    class FakeManager:
        def probe(self, path):
            calls.append(("probe", path))
            return {"duration": 1.5}

        def waveform(self, source_path, output_path, *, overwrite):
            calls.append(("waveform", source_path, output_path, overwrite))
            return SimpleNamespace(command=["ffmpeg", "waveform"])

        def spectrogram(self, source_path, output_path, *, overwrite):
            calls.append(("spectrogram", source_path, output_path, overwrite))
            return SimpleNamespace(command=["ffmpeg", "spectrogram"])

    manifest = generate_waveform_manifest(
        source, output_dir, manager=FakeManager(), overwrite=True
    )

    manifest_path = output_dir / "sample.preview.manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["operation"] == "generate_waveform_manifest"
    assert payload["probe"] == {"duration": 1.5}
    assert [artifact["role"] for artifact in payload["artifacts"]] == [
        "waveform",
        "spectrogram",
    ]
    assert payload["commands"] == [["ffmpeg", "waveform"], ["ffmpeg", "spectrogram"]]
    assert manifest.metadata == {"preserves_source": True}
    assert calls[0] == ("probe", source.resolve())
    assert all(call[-1] is True for call in calls[1:])


def test_missing_source_is_reported(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="Media source not found"):
        generate_waveform_manifest(tmp_path / "missing.wav", tmp_path / "previews")
