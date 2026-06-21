from __future__ import annotations

from pathlib import Path

from huey.media.media_manager import CommandResult
from huey.v1.proof_loop import ProofLoop
from huey.v1.response_bridge import ResponseBridge
from huey.v1.structured_run_log import StructuredRunLog


class FakeAudioManager:
    def convert_audio(self, source, output, **kwargs):
        Path(output).write_bytes(b"converted")
        return CommandResult(0, "", "", ["ffmpeg", "convert"], Path(output))

    def normalize_audio(self, source, output, **kwargs):
        Path(output).write_bytes(b"normalized")
        return CommandResult(0, "", "", ["ffmpeg", "normalize"], Path(output))


def test_proof_loop_with_patched_audio(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "fixture.mp3"
    source.write_bytes(b"audio")

    def fake_prepare(source_audio, prepared_audio, **kwargs):
        from huey.media.speech_pipeline import prepare_audio_for_transcription

        return prepare_audio_for_transcription(
            source_audio,
            prepared_audio,
            manager=FakeAudioManager(),
            overwrite=True,
        )

    monkeypatch.setattr("huey.v1.proof_loop.prepare_audio_for_transcription", fake_prepare)
    log = StructuredRunLog(tmp_path / "run.jsonl")
    result = ProofLoop(response_bridge=ResponseBridge(), run_log=log).run(
        source,
        tmp_path / "out",
        transcript_text="hello huey",
        overwrite=True,
    )
    assert result.prepared_audio.exists()
    assert "hello huey" in result.response
    assert log.read()[0]["event_type"] == "proof_loop.completed"

