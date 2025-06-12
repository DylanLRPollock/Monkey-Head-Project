from __future__ import annotations

import subprocess
from typing import Sequence, Optional

from .logger import get_logger
from ..core.system_checks import check_error

logger = get_logger(__name__)


def run_command(
    cmd: Sequence[str], *, cwd: Optional[str] = None, check: bool = True
) -> subprocess.CompletedProcess:
    """Run a system command and optionally verify it succeeded."""
    logger.debug("Running command: %s", " ".join(cmd))
    kwargs = {"stdout": subprocess.PIPE, "stderr": subprocess.PIPE}
    if cwd is not None:
        kwargs["cwd"] = cwd
    result = subprocess.run(list(cmd), **kwargs)
    if check:
        check_error(result, " ".join(cmd))
    return result
