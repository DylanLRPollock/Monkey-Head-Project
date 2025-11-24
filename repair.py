# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Repair utility

"""Repair utility that reinstalls the project from a repository.

This module provides a single entry point, :func:`run_repair`, which:

1. Invokes the local uninstaller to remove the current installation.
2. Clones a fresh copy of the repository into a temporary directory.
3. Runs ``installer.py`` from that checkout using the current Python interpreter.

The function always returns an integer exit code:

- ``0`` indicates success.
- Any non-zero value indicates a failure at some stage of the process.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import uninstaller


def _run(
    args: list[str],
    *,
    cwd: Path | None = None,
    capture_output: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Internal helper to run a subprocess without raising on failure.

    Parameters
    ----------
    args:
        Command and arguments to execute, e.g. ``["git", "clone", ...]``.
    cwd:
        Optional working directory for the subprocess.
    capture_output:
        If ``True``, captures stdout/stderr as text for diagnostics.
        If ``False``, inherits the parent process' stdio.

    Returns
    -------
    subprocess.CompletedProcess[str]
        The completed process object with ``returncode``, ``stdout`` and
        ``stderr`` (the latter two only populated when ``capture_output`` is
        enabled).
    """
    try:
        return subprocess.run(
            args,
            cwd=str(cwd) if cwd is not None else None,
            text=True,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.PIPE if capture_output else None,
            check=False,
        )
    except OSError as exc:
        # Normalise OS-level failures (e.g. command not found) into a
        # synthetic CompletedProcess with a non-zero return code.
        return subprocess.CompletedProcess(
            args=args,
            returncode=1,
            stdout="",
            stderr=f"{type(exc).__name__}: {exc}",
        )


def run_repair(repo_url: str) -> int:
    """Reinstall HueyOS from a Git repository.

    This function performs a best-effort repair of the local installation:

    1. Calls :func:`uninstaller.run_uninstaller` to tear down any existing
       installation. If that step fails (non-zero exit code), the repair
       aborts immediately and that code is returned.
    2. Creates a temporary directory and performs a shallow clone
       (``--depth 1``) of ``repo_url`` into it.
    3. Locates ``installer.py`` in the checkout root and invokes it with the
       current Python interpreter (``sys.executable``).
    4. Returns the installer exit code, or a non-zero value if any step fails.

    Parameters
    ----------
    repo_url:
        The Git URL (HTTPS/SSH/file) of the HueyOS repository to clone.

    Returns
    -------
    int
        Exit code suitable for use as a process status:

        * ``0`` – repair succeeded end-to-end.
        * Non-zero – an error occurred in the uninstaller, clone, or install
          phase. In case of clone or install failures, basic diagnostics are
          written to ``sys.stderr`` when available.
    """
    # Step 1: run the uninstaller first. If it fails, we stop here and bubble
    # up the exact code it returned so callers can see what went wrong.
    try:
        uninstall_code = uninstaller.run_uninstaller()
    except Exception:  # Defensive: uninstaller should not raise, but do not crash.
        return 1

    if uninstall_code != 0:
        return uninstall_code

    # Step 2: clone the repository into a temporary directory.
    with tempfile.TemporaryDirectory() as tmpdir:
        checkout = Path(tmpdir)

        clone = _run(
            ["git", "clone", "--depth", "1", repo_url, str(checkout)],
            cwd=None,
            capture_output=True,
        )
        if clone.returncode != 0:
            # Surface any useful diagnostics to stderr to help with debugging.
            if clone.stderr:
                sys.stderr.write(clone.stderr)
            return clone.returncode

        # Step 3: locate and run installer.py from the freshly cloned tree.
        installer = checkout / "installer.py"
        if not installer.is_file():
            # No installer script present; fail with a generic non-zero code.
            sys.stderr.write(
                f"repair: expected installer.py at {installer!s} but it was not found.\n"
            )
            return 1

        install = _run(
            [sys.executable, str(installer)],
            cwd=checkout,
            capture_output=False,
        )
        return install.returncode


__all__ = ["run_repair"]