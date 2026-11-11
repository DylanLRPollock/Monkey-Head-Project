"""Cover command-line path selection, output, and error handling."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from huey.media import cli_audio_prepare as cli


def test_output_path_selection_and_defaults(tmp_path):
    source = tmp_path / "lecture.mp3"
    assert cli._default_output_path(source) == tmp_path / "lecture.prepared.wav"
    assert cli._default_output_path(source, output_dir=tmp_path / "out") == (
        tmp_path / "out" / "lecture.prepared.wav"
    )
    assert (
        cli._resolve_output_path(source, destination=None, output=None, output_dir=None)
        == tmp_path / "lecture.prepared.wav"
    )
    assert (
        cli._resolve_output_path(
            source, destination="~/explicit.wav", output=None, output_dir=None
        )
        == Path("~/explicit.wav").expanduser().resolve()
    )
    assert (
        cli._resolve_output_path(
            source, destination="~/dir", output=None, output_dir=None
        )
        == Path("~/dir/lecture.prepared.wav").expanduser().resolve()
    )
    assert (
        cli._resolve_output_path(
            source, destination=None, output="~/chosen.wav", output_dir=None
        )
        == Path("~/chosen.wav").expanduser().resolve()
    )
    assert (
        cli._resolve_output_path(
            source, destination=None, output=None, output_dir="~/chosen"
        )
        == Path("~/chosen/lecture.prepared.wav").expanduser().resolve()
    )
    assert cli._resolve_manifest_path(None, output_path=source) is None
    assert cli._resolve_manifest_path("~/manifest.json", output_path=source) == (
        Path("~/manifest.json").expanduser().resolve()
    )
    assert cli._resolve_manifest_path("~/manifests", output_path=source) == (
        Path("~/manifests/lecture.manifest.json").expanduser().resolve()
    )


def test_output_selector_conflicts_are_rejected(tmp_path):
    with pytest.raises(ValueError, match="Choose only one"):
        cli._resolve_output_path(
            tmp_path / "source.mp3",
            destination="out.wav",
            output="other.wav",
            output_dir=None,
        )


def _fake_manifest(output: Path):
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(b"wav")
    artifact = SimpleNamespace(path=str(output))

    def write_manifest(path, overwrite=False):
        manifest_path = Path(path)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        return manifest_path.write_text(
            json.dumps({"operation": "prepare"}), encoding="utf-8"
        )

    return SimpleNamespace(
        artifacts=[artifact],
        to_dict=lambda: {"operation": "prepare", "artifacts": [str(output)]},
        write_json=write_manifest,
    )


def test_main_success_json_and_text_output(tmp_path, monkeypatch, capsys):
    source = tmp_path / "source.mp3"
    source.write_bytes(b"audio")
    output = tmp_path / "prepared.wav"
    monkeypatch.setattr(
        cli, "prepare_audio_for_transcription", lambda *a, **k: _fake_manifest(output)
    )

    assert cli.main([str(source), "--output", str(output), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "huey.audio.preparation.result"
    assert payload["exists"] is True
    assert payload["manifest_path"] is None

    assert (
        cli.main(
            [
                str(source),
                "--output-dir",
                str(tmp_path / "out"),
                "--manifest",
                str(tmp_path / "manifests"),
            ]
        )
        == 0
    )
    output_text = capsys.readouterr().out
    assert "Prepared transcription WAV:" in output_text
    assert "Manifest:" in output_text
    assert (tmp_path / "manifests" / "source.prepared.manifest.json").exists()

    assert cli.main([str(source)]) == 0
    output_text = capsys.readouterr().out
    assert "Prepared transcription WAV:" in output_text
    assert "Manifest:" not in output_text


@pytest.mark.parametrize(
    ("argv", "error"),
    [
        (["missing.mp3"], "Source audio file does not exist"),
    ],
)
def test_main_reports_missing_source(argv, error, capsys):
    assert cli.main(argv) == 2
    assert error in capsys.readouterr().err


def test_main_reports_existing_output_and_invalid_arguments(tmp_path, capsys):
    source = tmp_path / "source.mp3"
    source.touch()
    output = tmp_path / "already.wav"
    output.touch()
    assert cli.main([str(source), "--output", str(output)]) == 2
    assert "Refusing to overwrite" in capsys.readouterr().err
    assert cli.main([str(source), "--output", "one.wav", "--output-dir", "out"]) == 2
    assert "Choose only one" in capsys.readouterr().err


@pytest.mark.parametrize(
    "exception",
    [
        FileNotFoundError("missing"),
        FileExistsError("exists"),
        ValueError("bad"),
        RuntimeError("failed"),
    ],
)
def test_main_reports_pipeline_errors(tmp_path, monkeypatch, capsys, exception):
    source = tmp_path / "source.mp3"
    source.touch()

    def fail(*args, **kwargs):
        raise exception

    monkeypatch.setattr(cli, "prepare_audio_for_transcription", fail)
    assert cli.main([str(source)]) == 2
    assert f"error: {exception}" in capsys.readouterr().err
