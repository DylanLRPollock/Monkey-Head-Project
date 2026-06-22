"""Mock-first response bridge for the HueyOS V1 proof path."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class ResponseResult:
    """Response bridge output."""

    mode: str
    prompt: str
    response: str
    created_at: str

    def to_json_dict(self) -> dict[str, Any]:
        """Return JSON-safe result data."""

        return {
            "mode": self.mode,
            "prompt": self.prompt,
            "response": self.response,
            "created_at": self.created_at,
        }


class ResponseBridge:
    """Bridge text prompts to mock, local, or API-backed responders."""

    def __init__(self, mode: str = "mock") -> None:
        if mode not in {"mock", "api"}:
            raise ValueError("mode must be 'mock' or 'api'")
        self.mode = mode

    def respond(self, prompt: str) -> ResponseResult:
        """Return a response without hidden network calls."""

        if not prompt.strip():
            raise ValueError("prompt is required")
        if self.mode == "api":
            response = self._api_response(prompt)
        else:
            response = f"[mock] Huey V1 received: {prompt.strip()}"
        return ResponseResult(
            mode=self.mode,
            prompt=prompt,
            response=response,
            created_at=datetime.now(UTC).isoformat(),
        )

    def _api_response(self, prompt: str) -> str:
        api_key = os.getenv("HUEY_RESPONSE_API_KEY")
        if not api_key:
            raise RuntimeError("HUEY_RESPONSE_API_KEY is required for api mode")
        return f"[api placeholder] credential present; prompt length={len(prompt)}"


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt")
    parser.add_argument("--mode", choices=("mock", "api"), default="mock")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = ResponseBridge(args.mode).respond(args.prompt)
    print(
        json.dumps(result.to_json_dict(), indent=2, sort_keys=True)
        if args.json
        else result.response
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
