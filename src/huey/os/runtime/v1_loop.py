"""CI-safe V1 proof-loop orchestration.

V1 target:
controlled MP3 fixture -> local transcription -> cognition bridge -> structured log
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from uuid import uuid4


def _to_iso8601_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def run_v1_loop(
    source_fixture_path: str | Path,
    transcribe_func,
    cognition_func,
    log_writer,
) -> dict:
    """Run the CI-safe V1 orchestration with injected dependencies.

    The function never calls real external APIs/models itself; all behavior is
    delegated to injected callables.
    """
    start_dt = datetime.now(tz=UTC)
    start_perf = perf_counter()
    source_file = str(source_fixture_path)

    run_record = {
        "run_id": str(uuid4()),
        "timestamp_start": _to_iso8601_utc(start_dt),
        "timestamp_end": None,
        "source_file": source_file,
        "transcription_engine": None,
        "transcription_model": None,
        "transcript": None,
        "cognition_provider": None,
        "cognition_model": None,
        "response": None,
        "runtime_seconds": None,
        "exit_status": "error",
        "error_message_if_any": None,
    }

    try:
        transcription_result = transcribe_func(source_file)
        if isinstance(transcription_result, dict):
            run_record["transcription_engine"] = transcription_result.get(
                "transcription_engine"
            )
            run_record["transcription_model"] = transcription_result.get(
                "transcription_model"
            )
            run_record["transcript"] = transcription_result.get("transcript")
        else:
            run_record["transcript"] = str(transcription_result)

        cognition_result = cognition_func(run_record["transcript"])
        if isinstance(cognition_result, dict):
            run_record["cognition_provider"] = cognition_result.get(
                "cognition_provider"
            )
            run_record["cognition_model"] = cognition_result.get("cognition_model")
            run_record["response"] = cognition_result.get("response")
        else:
            run_record["response"] = str(cognition_result)

        run_record["exit_status"] = "success"
    except (OSError, ValueError, TypeError, RuntimeError) as exc:
        run_record["error_message_if_any"] = str(exc)

    end_dt = datetime.now(tz=UTC)
    run_record["timestamp_end"] = _to_iso8601_utc(end_dt)
    run_record["runtime_seconds"] = round(perf_counter() - start_perf, 6)

    log_writer(run_record)
    return run_record
