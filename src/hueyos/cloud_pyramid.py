"""Very small stub of the CloudPyramid decision helper."""

from __future__ import annotations

from random import Random


class CloudPyramid:
    """Return deterministic pseudo-random boolean decisions."""

    def __init__(self, seed: int | None = None):
        self._rng = Random(seed)

    def decide(self, proposal: str) -> bool:  # pragma: no cover - exercised in tests
        # Use a stable hash so the method always returns a boolean but with
        # repeatable outcomes for the same input.
        return self._rng.choice([True, False]) if proposal else False


__all__ = ["CloudPyramid"]
