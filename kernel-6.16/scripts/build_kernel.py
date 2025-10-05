#!/usr/bin/env python3
"""Build a customized Linux 6.16.x kernel.

This script automates the process of downloading Linux kernel sources, applying
an opinionated configuration, and building Debian packages suitable for
installation on Debian/Ubuntu based systems.  It is intentionally conservative
and aims to be easy to audit.  Most heavy lifting is delegated to the upstream
`make bindeb-pkg` target.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import shutil
import subprocess
import sys
import textwrap
from typing import Iterable, Sequence

KERNEL_SERIES = "6.16"
DEFAULT_VERSION = "6.16.12"
KERNEL_BASE_URL = "https://cdn.kernel.org/pub/linux/kernel/v6.x"


class CommandError(RuntimeError):
    """Raised when an external command exits with a failure status."""


def run_command(
    cmd: Sequence[str], *, cwd: pathlib.Path | None = None, env: dict[str, str] | None = None
) -> None:
    """Execute *cmd* and raise :class:`CommandError` if it fails."""

    try:
        subprocess.run(cmd, check=True, cwd=cwd, env=env)
    except subprocess.CalledProcessError as exc:  # pragma: no cover - defensive
        raise CommandError(f"Command failed with exit code {exc.returncode}: {cmd}") from exc


def ensure_directory(path: pathlib.Path) -> None:
    """Create *path* (and parents) when missing."""

    path.mkdir(parents=True, exist_ok=True)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download and build a custom Linux kernel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            f"""
            Examples:
              {pathlib.Path(sys.argv[0]).name} --version {DEFAULT_VERSION}
              {pathlib.Path(sys.argv[0]).name} --version {DEFAULT_VERSION} --clean
            """
        ),
    )
    parser.add_argument(
        "--version",
        default=DEFAULT_VERSION,
        help="Kernel version to build (must be within the 6.16.x series).",
    )
    parser.add_argument(
        "--config",
        default=pathlib.Path(__file__).resolve().parents[1] / "configs" / "custom-kernel.config",
        type=pathlib.Path,
        help="Path to the kernel .config file to apply before building.",
    )
    parser.add_argument(
        "--output",
        default=pathlib.Path(__file__).resolve().parents[1] / "artifacts",
        type=pathlib.Path,
        help="Directory where build artifacts (Debian packages) are stored.",
    )
    parser.add_argument(
        "--jobs",
        "-j",
        default=os.cpu_count() or 1,
        type=int,
        help="Number of parallel jobs to use for make.",
    )
    parser.add_argument(
        "--workdir",
        default=pathlib.Path(__file__).resolve().parents[1] / "worktrees",
        type=pathlib.Path,
        help="Directory that hosts kernel source trees.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove the worktree for the selected version and exit.",
    )
    parser.add_argument(
        "extra_make_args",
        nargs=argparse.REMAINDER,
        help="Additional arguments forwarded to 'make bindeb-pkg'.",
    )
    return parser.parse_args(argv)


def validate_version(version: str) -> None:
    pattern = rf"^{re.escape(KERNEL_SERIES)}\\.\\d+$"
    if not re.match(pattern, version):
        raise SystemExit(
            f"Unsupported kernel version '{version}'. Only the {KERNEL_SERIES}.x series is allowed."
        )


def download_kernel(version: str, tarball_dir: pathlib.Path) -> pathlib.Path:
    ensure_directory(tarball_dir)
    tarball_name = f"linux-{version}.tar.xz"
    tarball_path = tarball_dir / tarball_name
    if tarball_path.exists():
        return tarball_path

    url = f"{KERNEL_BASE_URL}/{tarball_name}"
    print(f"Downloading {url} -> {tarball_path}")
    run_command(["wget", "-O", str(tarball_path), url])
    return tarball_path


def extract_kernel(tarball: pathlib.Path, workdir: pathlib.Path, version: str) -> pathlib.Path:
    ensure_directory(workdir)
    source_dir = workdir / f"linux-{version}"
    if source_dir.exists():
        return source_dir

    print(f"Extracting {tarball} -> {source_dir}")
    run_command(["tar", "xf", str(tarball), "-C", str(workdir)])
    return source_dir


def copy_config(config_path: pathlib.Path, source_dir: pathlib.Path) -> None:
    target_config = source_dir / ".config"
    if not config_path.exists():
        raise SystemExit(f"Configuration file not found: {config_path}")

    print(f"Copying {config_path} -> {target_config}")
    shutil.copy2(config_path, target_config)


def prepare_kernel_tree(source_dir: pathlib.Path) -> None:
    print("Preparing kernel configuration (make olddefconfig)")
    run_command(["make", "olddefconfig"], cwd=source_dir)


def build_kernel(source_dir: pathlib.Path, output_dir: pathlib.Path, jobs: int, extra_args: Iterable[str]) -> None:
    ensure_directory(output_dir)
    env = os.environ.copy()
    env.setdefault("LOCALVERSION", "-monkey-head")

    make_cmd = [
        "make",
        f"-j{jobs}",
        "bindeb-pkg",
        f"KDEB_CHANGELOG_DIST={env.get('KDEB_CHANGELOG_DIST', 'custom')}",
    ]
    make_cmd.extend(extra_args)
    print("Running", " ".join(make_cmd))
    run_command(make_cmd, cwd=source_dir, env=env)

    # Move resulting .deb files next to output_dir if they were written to ..
    parent = source_dir.parent
    for artifact in parent.glob("*.deb"):
        destination = output_dir / artifact.name
        print(f"Moving {artifact} -> {destination}")
        shutil.move(str(artifact), destination)

    for metadata in parent.glob("*.buildinfo"):
        destination = output_dir / metadata.name
        print(f"Moving {metadata} -> {destination}")
        shutil.move(str(metadata), destination)

    for changes in parent.glob("*.changes"):
        destination = output_dir / changes.name
        print(f"Moving {changes} -> {destination}")
        shutil.move(str(changes), destination)


def clean_version(workdir: pathlib.Path, version: str) -> None:
    source_dir = workdir / f"linux-{version}"
    if source_dir.exists():
        print(f"Removing {source_dir}")
        shutil.rmtree(source_dir)
    else:
        print(f"Nothing to clean for {version}")


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    validate_version(args.version)

    workdir = pathlib.Path(args.workdir)
    output_dir = pathlib.Path(args.output)
    tarball_dir = workdir / "tarballs"

    if args.clean:
        clean_version(workdir, args.version)
        return 0

    tarball = download_kernel(args.version, tarball_dir)
    source_dir = extract_kernel(tarball, workdir, args.version)
    copy_config(args.config, source_dir)
    prepare_kernel_tree(source_dir)
    build_kernel(source_dir, output_dir, args.jobs, args.extra_make_args or [])

    print("\nBuild complete! Debian packages are located in:", output_dir)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    sys.exit(main(sys.argv[1:]))
