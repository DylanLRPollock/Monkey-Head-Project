"""Router package scaffold for the gradual ``hueyos.api`` split.

Next split step:
- Move a low-risk read-only endpoint group (for example health/system status)
  into dedicated router modules and include them from ``hueyos.api.app``.
"""

from __future__ import annotations

__all__: list[str] = []
