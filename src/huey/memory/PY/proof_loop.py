"""Coordinator for the active HueyOS V1 proof path."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from huey.media.speech_pipeline import prepare_audio_for_transcription
from huey.v1.response_bridge import ResponseBridge
from huey.v1.structured_run_log import StructuredRunLog


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
            self.run_log.append("proof_loop.completed", {
                "result": result.to_json_dict(),
                "audio_manifest": manifest.to_json_dict(),
                "response": response.to_json_dict(),
            })
        return result


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""

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
    print(json.dumps(result.to_json_dict(), indent=2, sort_keys=True) if args.json else result.response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

