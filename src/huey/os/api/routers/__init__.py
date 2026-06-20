"""Router package scaffold for the gradual ``huey.os.api`` split.

Next split step:
- Move a low-risk read-only endpoint group (for example health/system status)
  into dedicated router modules and include them from ``huey.os.api.app``.
"""

from __future__ import annotations

__all__: list[str] = []
