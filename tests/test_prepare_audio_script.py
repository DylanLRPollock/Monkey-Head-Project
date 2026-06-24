from __future__ import annotations

import json
from pathlib import Path

from huey.media.media_manifest import MediaArtifact, MediaManifest
from scripts import prepare_audio_for_transcription as prepare_audio_script


def _build_manifest(source: Path, output: Path) -> MediaManifest:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(b"prepared")
    return MediaManifest(
        source_path=str(source),
        operation="prepare_audio_for_transcription",
        artifacts=[
            MediaArtifact(
                kind="audio",
                path=str(output),
                role="transcription_wav",
                metadata={"channels": 1, "sample_rate_hz": 16000},
            )
        ],
        metadata={
            "pipeline": {
                "input": {"path": str(source)},
                "processing": {"steps": [{"id": "convert_to_mono_16khz_wav"}]},
            }
        },
    )


def test_script_defaults_output_and_emits_manifest_json(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    source = tmp_path / "fixture.mp3"
    source.write_bytes(b"audio")
    captured: dict[str, Path] = {}

    def fake_prepare(source_path, output_path, overwrite=False):
        del overwrite
        captured["source"] = Path(source_path)
        captured["output"] = Path(output_path)
        return _build_manifest(captured["source"], captured["output"])

    monkeypatch.setattr(
        prepare_audio_script,
        "prepare_audio_for_transcription",
        fake_prepare,
    )

    exit_code = prepare_audio_script.main([str(source), "--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert captured["source"] == source.resolve()
    assert captured["output"] == source.with_name("fixture.prepared.wav").resolve()
    assert Path(payload["output_path"]) == captured["output"]
    assert payload["manifest"]["metadata"]["pipeline"]["input"]["path"] == str(
        source.resolve()
    )


def test_script_treats_legacy_destination_without_suffix_as_output_dir(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    source = tmp_path / "fixture.mp3"
    source.write_bytes(b"audio")
    output_dir = tmp_path / "prepared"
    captured: dict[str, Path] = {}

    def fake_prepare(source_path, output_path, overwrite=False):
        del overwrite
        captured["source"] = Path(source_path)
        captured["output"] = Path(output_path)
        return _build_manifest(captured["source"], captured["output"])

    monkeypatch.setattr(
        prepare_audio_script,
        "prepare_audio_for_transcription",
        fake_prepare,
    )

    exit_code = prepare_audio_script.main([str(source), str(output_dir), "--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert captured["output"] == (output_dir / "fixture.prepared.wav").resolve()
    assert Path(payload["output_path"]) == captured["output"]
