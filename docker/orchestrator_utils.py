"""Shared helpers for Monkey Head orchestrator scripts."""
from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple

log = logging.getLogger("orchestrator")


class CommandError(RuntimeError):
    """Raised when a subprocess invocation fails."""


def run(
    cmd: Sequence[str],
    *,
    check: bool = True,
    capture_output: bool = True,
    text: bool = True,
    logger: Optional[logging.Logger] = None,
    **popen_kwargs,
) -> subprocess.CompletedProcess[str]:
    """Execute *cmd* and return the completed process.

    Parameters mirror :func:`subprocess.run` with sane defaults for CLI tooling.
    When *check* is true and the command exits with a non-zero status, a
    :class:`CommandError` is raised with stdout/stderr included to aid debugging.
    """

    if logger is None:
        logger = log

    logger.debug("→ %s", " ".join(cmd))
    completed = subprocess.run(
        cmd,
        check=False,
        capture_output=capture_output,
        text=text,
        **popen_kwargs,
    )
    if check and completed.returncode != 0:
        logger.error(
            "Command failed (%s): %s\nstdout:\n%s\nstderr:\n%s",
            completed.returncode,
            " ".join(cmd),
            completed.stdout,
            completed.stderr,
        )
        raise CommandError(f"Command failed ({completed.returncode}): {' '.join(cmd)}")
    return completed


def _parse_os_release() -> Tuple[str, str, Tuple[str, ...], str, str]:
    """Return ``(id, version_id, id_like, codename, pretty_name)``."""

    distro_id = "unknown"
    version_id = ""
    id_like: Tuple[str, ...] = ()
    codename = ""
    pretty_name = ""
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as handle:
            for line in handle:
                if "=" not in line:
                    continue
                key, value = line.strip().split("=", 1)
                value = value.strip().strip('"')
                key = key.upper()
                if key == "ID":
                    distro_id = value.lower()
                elif key == "VERSION_ID":
                    version_id = value.lower()
                elif key == "ID_LIKE":
                    id_like = tuple(part.lower() for part in value.split())
                elif key == "VERSION_CODENAME":
                    codename = value.lower()
                elif key == "PRETTY_NAME":
                    pretty_name = value
    except FileNotFoundError:
        pass
    return distro_id, version_id, id_like, codename.lower() if codename else "", pretty_name


def ensure_system_requirements(
    *,
    component_name: str,
    skip_os_check: bool,
    allowed_distributions: Optional[Iterable[str]] = None,
    min_free_gib: float = 5.0,
    ping_hosts: Optional[Sequence[str]] = None,
    logger: Optional[logging.Logger] = None,
) -> None:
    """Perform shared system validation for orchestrators."""

    if logger is None:
        logger = log

    logger.info("Performing system checks for %s…", component_name)

    distro_id, version_id, id_like, codename, pretty = _parse_os_release()
    pretty_for_display = pretty or codename or version_id or distro_id
    if not skip_os_check and allowed_distributions:
        target_pairs = []
        for item in allowed_distributions:
            base, _, name = item.lower().partition(":")
            target_pairs.append((base, name))
        matches = False
        name_candidates = {value for value in (version_id, codename) if value}
        if pretty:
            name_candidates.add(pretty.lower())
        for base, name in target_pairs:
            if base not in {distro_id, *id_like}:
                continue
            if not name or name in name_candidates:
                matches = True
                break
            if name == "stable" and distro_id == "debian":
                matches = True
                break
            if name == "testing" and distro_id == "debian":
                matches = True
                break
        if not matches:
            raise RuntimeError(
                "Unsupported distribution detected: "
                f"{pretty_for_display or 'unknown'} (ID={distro_id}, VERSION_ID={version_id or 'n/a'}, "
                f"CODENAME={codename or 'n/a'}). Allowed: {', '.join(allowed_distributions)}."
            )
    elif skip_os_check:
        logger.warning("Skipping OS compatibility validation as requested.")

    usage = shutil.disk_usage("/")
    free_gib = usage.free / (1024 ** 3)
    logger.info("Free space on /: %.2f GiB", free_gib)
    if free_gib < min_free_gib:
        raise RuntimeError(
            f"Insufficient free disk space for {component_name}: "
            f"requires at least {min_free_gib:.1f} GiB."
        )

    ping_targets = ping_hosts or ("1.1.1.1", "8.8.8.8", "google.com")
    for host in ping_targets:
        try:
            probe = run(["ping", "-c", "1", "-W", "2", host], check=False, logger=logger)
        except CommandError:
            continue
        if probe.returncode == 0:
            logger.info("Internet connectivity confirmed via %s", host)
            break
    else:
        raise RuntimeError("Internet connectivity check failed for all configured targets.")

    if shutil.which("git") is None:
        logger.warning("git not found; it will be installed during the apt stage.")


def apt_install(packages: Iterable[str], *, logger: Optional[logging.Logger] = None) -> None:
    """Install *packages* using apt-get with ``--no-install-recommends``."""

    if logger is None:
        logger = log

    deduped = sorted({pkg for pkg in packages if pkg})
    if not deduped:
        logger.info("No packages requested for installation.")
        return
    logger.info("Installing packages via apt: %s", ", ".join(deduped))
    run(["sudo", "apt-get", "update"], logger=logger)
    run(
        ["sudo", "apt-get", "install", "-y", "--no-install-recommends", *deduped],
        logger=logger,
    )


def ensure_workspace(path: Path, env_var: str, *, logger: Optional[logging.Logger] = None) -> None:
    """Create *path* and append an environment export to ~/.bashrc if missing."""

    if logger is None:
        logger = log

    path = path.expanduser().resolve()
    logger.info("Ensuring workspace exists at %s", path)
    path.mkdir(parents=True, exist_ok=True)

    bashrc = Path.home() / ".bashrc"
    export_line = f"export {env_var}={path}\n"
    if bashrc.exists():
        content = bashrc.read_text()
        if export_line.strip() not in content:
            bashrc.write_text(content.rstrip("\n") + "\n" + export_line)
            logger.debug("Added %s export to %s", env_var, bashrc)
    else:
        bashrc.write_text(export_line)
        logger.debug("Created %s with %s export", bashrc, env_var)


def configure_firewall(
    port: int,
    *,
    protocol: str = "tcp",
    comment: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> None:
    """Ensure a UFW rule exists for ``port/protocol``."""

    if logger is None:
        logger = log

    if shutil.which("ufw") is None:
        logger.warning("ufw not installed; skipping firewall configuration.")
        return

    logger.info("Ensuring UFW allows %s/%s", port, protocol)
    status = run(["sudo", "ufw", "status"], check=False, logger=logger)
    if f"{port}/{protocol}" in status.stdout:
        logger.debug("UFW already allows %s/%s", port, protocol)
        return

    cmd = ["sudo", "ufw", "allow", f"{port}/{protocol}"]
    if comment:
        cmd.extend(["comment", comment])
    run(cmd, check=False, logger=logger)


__all__ = [
    "CommandError",
    "apt_install",
    "configure_firewall",
    "ensure_system_requirements",
    "ensure_workspace",
    "run",
]
