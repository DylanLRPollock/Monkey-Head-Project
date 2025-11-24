# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Fresh install module
"""Entry point to perform a clean installation."""

from __future__ import annotations

import installer
import repair
import uninstaller


def run_fresh_install(source: str = "local", repo_url: str | None = None) -> int:
    result = uninstaller.run_uninstaller()
    if result != 0:
        return result

    if source == "github" and repo_url:
        return repair.run_repair(repo_url)
    return installer.run_installer()


__all__ = ["run_fresh_install"]
