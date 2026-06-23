"""Higher-level V1 fixture orchestration built on the CI-safe runtime loop."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from huey.audio.transcription_pipeline import transcribe
from huey.media.speech_pipeline import prepare_audio_for_transcription
from huey.os.runtime.v1_loop import run_v1_loop
from huey.utils.paths import ensure_subdirectory
from huey.v1.fixture_registry import list_fixtures, load_fixture
from huey.v1.response_bridge import ResponseBridge
from huey.v1.structured_run_log import StructuredRunLog

CognitionFunc = Callable[[str], dict[str, str] | str]
TranscribeFunc = Callable[[str], dict[str, object] | str]


@dataclass(frozen=True)
class ProofLoopResult:
    """Result of one V1 proof-loop run."""

    source_audio: Path
    prepared_audio: Path
    transcript: str
    response: str
    created_at: str

    def to_json_dict(self) -> dict[str, Any]:
        """Return JSON-safe proof-loop data."""

        return {
            "source_audio": str(self.source_audio),
            "prepared_audio": str(self.prepared_audio),
            "transcript": self.transcript,
            "response": self.response,
            "created_at": self.created_at,
        }


class ProofLoop:
    """Run the known fixture to preparation to response to log path."""

    def __init__(
        self,
        *,
        response_bridge: ResponseBridge | None = None,
        run_log: StructuredRunLog | None = None,
    ) -> None:
        self.response_bridge = response_bridge or ResponseBridge(mode="mock")
        self.run_log = run_log

    def run(
        self,
        source_audio: Path,
        output_dir: Path,
        *,
        transcript_text: str | None = None,
        overwrite: bool = False,
    ) -> ProofLoopResult:
        """Run one auditable V1 proof-loop iteration."""

        source_audio = Path(source_audio)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        prepared_audio = output_dir / f"{source_audio.stem}_prepared.wav"
        manifest = prepare_audio_for_transcription(
            source_audio,
            prepared_audio,
            overwrite=overwrite,
        )
        transcript = transcript_text or f"Prepared audio fixture: {source_audio.name}"
        response = self.response_bridge.respond(transcript)
        result = ProofLoopResult(
            source_audio=source_audio,
            prepared_audio=prepared_audio,
            transcript=transcript,
            response=response.response,
            created_at=datetime.now(UTC).isoformat(),
        )
        if self.run_log:
            self.run_log.append(
                "proof_loop.completed",
                {
                    "result": result.to_json_dict(),
                    "audio_manifest": manifest.to_json_dict(),
                    "response": response.to_json_dict(),
                },
            )
        return result


def _default_cognition(transcript: str | None) -> dict[str, str]:
    summary = (transcript or "").strip()[:160]
    return {
        "cognition_provider": "offline-stub",
        "cognition_model": "rule-based-summary",
        "response": f"Processed fixture transcript: {summary or 'no transcript available'}",
    }


def _default_log_dir(path: Path | None = None) -> Path:
    selected = path or ensure_subdirectory("V1", "runs")
    selected.mkdir(parents=True, exist_ok=True)
    return selected


def run_fixture(
    fixture: str | Path | dict[str, object],
    *,
    transcribe_func: TranscribeFunc | None = None,
    cognition_func: CognitionFunc | None = None,
    log_dir: str | Path | None = None,
    mock: bool = True,
) -> dict[str, object]:
    """Run the V1 fixture loop for a single source file."""

    if isinstance(fixture, dict):
        source_file = str(fixture["path"])
    else:
        source_file = str(Path(fixture).expanduser().resolve())
    selected_log_dir = _default_log_dir(Path(log_dir) if log_dir else None)
    jsonl_path = selected_log_dir / "v1-runs.jsonl"

    def _transcribe(source_path: str) -> dict[str, object] | str:
        if transcribe_func is not None:
            return transcribe_func(source_path)
        return transcribe(source_path, mock=mock)

    def _cognition(transcript_value: str | None) -> dict[str, str] | str:
        if cognition_func is not None:
            return cognition_func(transcript_value or "")
        return _default_cognition(transcript_value)

    def _log_writer(record: dict[str, object]) -> None:
        record_path = selected_log_dir / f"{record['run_id']}.json"
        record_path.write_text(
            json.dumps(record, indent=2, sort_keys=True), encoding="utf-8"
        )
        with jsonl_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True))
            handle.write("\n")

    return run_v1_loop(source_file, _transcribe, _cognition, _log_writer)


def run_all_fixtures(
    fixtures: list[str | Path] | None = None,
    *,
    fixture_ids: list[str] | None = None,
    log_dir: str | Path | None = None,
    mock: bool = True,
) -> list[dict[str, object]]:
    """Run the V1 loop across explicit or registered fixtures."""

    work_items: list[str | Path | dict[str, object]]
    if fixtures is not None:
        work_items = fixtures
    elif fixture_ids:
        work_items = [load_fixture(fixture_id) for fixture_id in fixture_ids]
    else:
        work_items = list_fixtures()
    return [run_fixture(item, log_dir=log_dir, mock=mock) for item in work_items]


def validate_result(run_record: dict[str, object]) -> bool:
    """Return ``True`` when a run record satisfies the V1 proof-loop contract."""

    return bool(
        run_record.get("exit_status") == "success"
        and run_record.get("transcript")
        and run_record.get("response")
    )


def generate_report(run_records: list[dict[str, object]]) -> dict[str, object]:
    """Return an aggregate summary for a batch of V1 runs."""

    total = len(run_records)
    successful = sum(1 for record in run_records if validate_result(record))
    failed = total - successful
    return {
        "total": total,
        "successful": successful,
        "failed": failed,
        "success_rate": (successful / total) if total else 0.0,
        "failed_runs": [
            record.get("run_id")
            for record in run_records
            if not validate_result(record)
        ],
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for the auditable proof-loop runner."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_audio", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--transcript-text")
    parser.add_argument("--log", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    log = StructuredRunLog(args.log) if args.log else None
    result = ProofLoop(run_log=log).run(
        args.source_audio,
        args.output_dir,
        transcript_text=args.transcript_text,
        overwrite=args.overwrite,
    )
    print(
        json.dumps(result.to_json_dict(), indent=2, sort_keys=True)
        if args.json
        else result.response
    )
    return 0


__all__ = [
    "ProofLoop",
    "ProofLoopResult",
    "generate_report",
    "main",
    "run_all_fixtures",
    "run_fixture",
    "validate_result",
]
