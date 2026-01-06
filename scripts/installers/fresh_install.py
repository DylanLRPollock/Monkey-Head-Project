# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Fresh install module

"""Entry point to perform a clean installation of HueyOS.

This helper performs a two-step operation:

1. Run the uninstaller to remove any existing installation.
2. Install HueyOS again using one of two paths:
   - Local install (default): call ``installer.run_installer()``.
   - GitHub install: if ``source == "github"`` and ``repo_url`` is provided,
     delegate to ``repair.run_repair(repo_url)`` which reclones the repository
     and runs the installer from that checkout.

The return value is the exit code from the final install/repair step, or a
non-zero code if the uninstall phase fails.
"""

from __future__ import annotations

from . import installer
from . import repair
from . import uninstaller


def run_fresh_install(source: str = "local", repo_url: str | None = None) -> int:
    """Perform a clean install and return the resulting exit code.

    Parameters
    ----------
    source:
        Installation source selector. ``"local"`` (default) uses the existing
        checkout and calls :func:`installer.run_installer`. If set to
        ``"github"`` and ``repo_url`` is provided, the function delegates to
        :func:`repair.run_repair`.
    repo_url:
        Optional repository URL used when ``source == "github"``. Ignored for
        other source values.

    Returns
    -------
    int
        Exit code from the uninstall + install process. A non-zero value
        indicates failure in either the uninstall or install phase.
    """
    result = uninstaller.run_uninstaller()
    if result != 0:
        return result

    if source == "github" and repo_url:
        return repair.run_repair(repo_url)

    return installer.run_installer()


__all__ = ["run_fresh_install"]
