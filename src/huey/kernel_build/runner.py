"""Audited subprocess adapter for the HueyOS kernel build framework.

This is the **only** module in the framework that launches subprocesses.
Every command execution flows through :class:`Runner`, which enforces:

* **argv arrays only.** No ``shell=True``, no ``eval``, no string
  interpolation. Callers build ``CommandSpec(argv=(...))`` explicitly.
  Shell metacharacters inside an argv element are inert strings, not
  shell syntax.
* **Whitelisted environment.** A small set of variables is inherited from
  the parent process (``PATH``, ``HOME``, ``TMPDIR``, ``USER``, ``LOGNAME``,
  ``LANG``, ``LC_*``, and reproducible-build variables). Callers may
  override. The resulting environment is recorded in
  ``CommandResult.env_summary`` with any variable whose name looks
  sensitive redacted to ``"<redacted>"`` via
  :func:`huey.kernel_build.models.redact_environment`.
* **Bounded time and output.** Every spec carries a positive timeout and
  stdout/stderr byte caps. Oversized output is truncated, flagged via
  ``RunnerResult.output_truncated``, and optionally raised as
  :class:`RunnerOutputTooLarge` when ``strict_output=True``.
* **Fail-closed dry run.** ``dry_run=True`` never launches a subprocess. It
  returns a :class:`RunnerResult` with ``executed=False`` and a
  :data:`DRY_RUN_RETURNCODE` sentinel exit code. ``cwd`` existence is not
  checked in dry-run mode.

Tests use :class:`FakeRunner`, which implements :class:`RunnerProtocol` and
returns pre-seeded :class:`RunnerResult` values without touching the host.
"""

from __future__ import annotations

import logging
import os
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Protocol

from huey.kernel_build.models import CommandResult, redact_environment

logger = logging.getLogger(__name__)

#: Sentinel returncode returned by ``Runner.run(..., dry_run=True)``.
#: Distinct from any real subprocess returncode (0..255 for normal exits on
#: POSIX, negative signal numbers in Python's representation) so callers can
#: reliably distinguish "not run" from "run and failed".
DRY_RUN_RETURNCODE: int = -9999

_BASE_ENV_WHITELIST: tuple[str, ...] = (
    "PATH",
    "HOME",
    "TMPDIR",
    "USER",
    "LOGNAME",
    "LANG",
    "SOURCE_DATE_EPOCH",  # reproducible builds
    "DEB_BUILD_OPTIONS",
    "DEB_HOST_ARCH",
    "DEB_BUILD_ARCH",
    "LD_LIBRARY_PATH",
)

_READ_CHUNK_BYTES = 64 * 1024
_THREAD_JOIN_TIMEOUT = 5.0

__all__ = [
    "CommandSpec",
    "DRY_RUN_RETURNCODE",
    "FakeRunner",
    "Runner",
    "RunnerError",
    "RunnerOutputTooLarge",
    "RunnerProtocol",
    "RunnerResult",
    "RunnerTimeout",
    "is_dry_run",
]


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class RunnerError(RuntimeError):
    """Base error for runner-level failures."""


class RunnerTimeout(RunnerError):
    """Subprocess did not exit within the configured timeout."""


class RunnerOutputTooLarge(RunnerError):
    """Subprocess output exceeded the configured byte limit (strict mode)."""


def is_dry_run(result: CommandResult) -> bool:
    """Return ``True`` when ``result`` came from a dry-run invocation."""
    return result.returncode == DRY_RUN_RETURNCODE


# ---------------------------------------------------------------------------
# CommandSpec
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CommandSpec:
    """Immutable description of a command to execute.

    ``argv`` is a tuple of strings; lists are accepted for convenience and
    normalized to tuples. ``cwd`` may be given as ``str`` or ``Path``.
    ``env_overrides`` are merged on top of the whitelisted base environment;
    the caller is responsible for supplying only safe values, since the
    environment summary recorded in ``CommandResult`` is redacted by name
    only.
    """

    argv: tuple[str, ...]
    cwd: Path
    description: str = ""
    env_overrides: Mapping[str, str] = field(default_factory=dict)
    timeout_seconds: float = 3600.0
    max_stdout_bytes: int = 16 * 1024 * 1024
    max_stderr_bytes: int = 16 * 1024 * 1024

    def __post_init__(self) -> None:
        argv = self.argv
        if isinstance(argv, list):
            argv = tuple(argv)
            object.__setattr__(self, "argv", argv)
        if not isinstance(argv, tuple) or not all(isinstance(a, str) for a in argv):
            raise TypeError("CommandSpec.argv must be tuple[str, ...]")
        if not argv:
            raise ValueError("CommandSpec.argv must be non-empty")
        if any(a == "" for a in argv):
            raise ValueError("CommandSpec.argv must not contain empty strings")

        cwd = self.cwd
        if isinstance(cwd, str):
            cwd = Path(cwd)
            object.__setattr__(self, "cwd", cwd)
        if not isinstance(cwd, Path):
            raise TypeError("CommandSpec.cwd must be Path or str")

        if not isinstance(self.timeout_seconds, (int, float)) or (
            self.timeout_seconds <= 0
        ):
            raise ValueError(
                "CommandSpec.timeout_seconds must be a positive number"
            )
        if not isinstance(self.max_stdout_bytes, int) or self.max_stdout_bytes < 1:
            raise ValueError(
                "CommandSpec.max_stdout_bytes must be a positive int"
            )
        if not isinstance(self.max_stderr_bytes, int) or self.max_stderr_bytes < 1:
            raise ValueError(
                "CommandSpec.max_stderr_bytes must be a positive int"
            )

        if not isinstance(self.env_overrides, Mapping):
            raise TypeError("CommandSpec.env_overrides must be a Mapping")
        for key, value in self.env_overrides.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise TypeError(
                    "CommandSpec.env_overrides keys and values must be str"
                )


# ---------------------------------------------------------------------------
# RunnerResult
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RunnerResult:
    """Result of a :class:`Runner` invocation.

    ``command`` carries the serializable, loggable record. ``stdout`` /
    ``stderr`` carry the (possibly truncated) captured bytes for in-memory
    inspection. ``executed`` and ``dry_run`` distinguish a real execution
    from a plan.
    """

    command: CommandResult
    executed: bool
    dry_run: bool
    stdout: bytes | None = None
    stderr: bytes | None = None
    output_truncated: bool = False

    @property
    def succeeded(self) -> bool:
        """True only for a real, non-truncated, zero-exit execution."""
        return (
            self.executed
            and not self.dry_run
            and not self.output_truncated
            and self.command.returncode == 0
        )


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


class RunnerProtocol(Protocol):
    """Minimal interface consumed by higher-level builders."""

    def run(
        self, spec: CommandSpec, *, dry_run: bool = False
    ) -> RunnerResult:
        ...


# ---------------------------------------------------------------------------
# Environment helpers
# ---------------------------------------------------------------------------


def _build_env(overrides: Mapping[str, str]) -> dict[str, str]:
    """Build a subprocess environment from the whitelist plus overrides."""
    env: dict[str, str] = {}
    for key in _BASE_ENV_WHITELIST:
        if key in os.environ:
            env[key] = os.environ[key]
    for key, value in os.environ.items():
        if key.startswith("LC_") and key not in env:
            env[key] = value
    env.update(overrides)
    return env


# ---------------------------------------------------------------------------
# Bounded pipe reading
# ---------------------------------------------------------------------------


def _drain_bounded(pipe, limit: int) -> tuple[bytes, bool]:
    """Read from ``pipe`` until EOF, keeping at most ``limit`` bytes.

    Returns ``(data, truncated)``. Even when truncated, the pipe is fully
    drained to prevent the child process from blocking on a full write
    buffer.
    """
    chunks: list[bytes] = []
    total = 0
    truncated = False
    while True:
        chunk = pipe.read(_READ_CHUNK_BYTES)
        if not chunk:
            break
        total += len(chunk)
        if truncated:
            continue
        if total > limit:
            keep = limit - (total - len(chunk))
            if keep > 0:
                chunks.append(chunk[:keep])
            truncated = True
        else:
            chunks.append(chunk)
    return b"".join(chunks), truncated


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


class Runner:
    """Audited subprocess runner.

    Parameters
    ----------
    log_dir:
        Optional directory for persisting captured stdout/stderr to files.
        When set, ``CommandResult.stdout_path`` / ``stderr_path`` point at
        these files; the in-memory bytes are still returned on
        :class:`RunnerResult` for inspection.
    log:
        Optional logger; defaults to the module logger.
    """

    def __init__(
        self,
        *,
        log_dir: Path | None = None,
        log: logging.Logger | None = None,
    ) -> None:
        self._log_dir = Path(log_dir) if log_dir is not None else None
        self._log = log or logger

    def run(
        self,
        spec: CommandSpec,
        *,
        dry_run: bool = False,
        strict_output: bool = False,
    ) -> RunnerResult:
        """Execute ``spec`` (or plan it when ``dry_run=True``).

        Raises
        ------
        RunnerError
            ``cwd`` missing or invalid, or the executable cannot be launched.
        RunnerTimeout
            Subprocess exceeded ``spec.timeout_seconds``.
        RunnerOutputTooLarge
            Output exceeded the byte cap **and** ``strict_output=True``.
        """
        env = _build_env(spec.env_overrides)
        env_summary = redact_environment(env)
        description = spec.description or " ".join(spec.argv[:2])

        # ----- dry run: no execution, no cwd validation ----------------
        if dry_run:
            self._log.info(
                "command.planned description=%r argv_len=%d cwd=%s",
                description,
                len(spec.argv),
                spec.cwd,
            )
            return RunnerResult(
                command=CommandResult(
                    argv=spec.argv,
                    cwd=str(spec.cwd),
                    returncode=DRY_RUN_RETURNCODE,
                    elapsed_seconds=0.0,
                    stdout_path=None,
                    stderr_path=None,
                    env_summary=env_summary,
                ),
                executed=False,
                dry_run=True,
            )

        # ----- real execution -----------------------------------------
        if not spec.cwd.exists():
            raise RunnerError(f"cwd does not exist: {spec.cwd}")
        if not spec.cwd.is_dir():
            raise RunnerError(f"cwd is not a directory: {spec.cwd}")

        self._log.info(
            "command.executing description=%r argv_len=%d cwd=%s",
            description,
            len(spec.argv),
            spec.cwd,
        )
        started = time.monotonic()

        try:
            proc = subprocess.Popen(
                list(spec.argv),
                cwd=str(spec.cwd),
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                close_fds=True,
            )
        except FileNotFoundError as exc:
            raise RunnerError(
                f"executable not found: {spec.argv[0]!r}"
            ) from exc
        except OSError as exc:
            raise RunnerError(
                f"failed to launch {spec.argv[0]!r}: {exc}"
            ) from exc

        stdout_box: list[tuple[bytes, bool]] = []
        stderr_box: list[tuple[bytes, bool]] = []

        def _read_stdout() -> None:
            assert proc.stdout is not None
            stdout_box.append(_drain_bounded(proc.stdout, spec.max_stdout_bytes))

        def _read_stderr() -> None:
            assert proc.stderr is not None
            stderr_box.append(_drain_bounded(proc.stderr, spec.max_stderr_bytes))

        t_out = threading.Thread(target=_read_stdout, daemon=True)
        t_err = threading.Thread(target=_read_stderr, daemon=True)
        t_out.start()
        t_err.start()

        try:
            returncode = proc.wait(timeout=spec.timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            proc.kill()
            proc.wait()
            t_out.join(timeout=_THREAD_JOIN_TIMEOUT)
            t_err.join(timeout=_THREAD_JOIN_TIMEOUT)
            elapsed = time.monotonic() - started
            self._log.error(
                "command.timeout description=%r timeout=%.1fs elapsed=%.2fs",
                description,
                spec.timeout_seconds,
                elapsed,
            )
            raise RunnerTimeout(
                f"command timed out after {spec.timeout_seconds}s: {spec.argv!r}"
            ) from exc

        t_out.join()
        t_err.join()

        elapsed = time.monotonic() - started
        stdout, stdout_trunc = stdout_box[0] if stdout_box else (b"", False)
        stderr, stderr_trunc = stderr_box[0] if stderr_box else (b"", False)
        truncated = stdout_trunc or stderr_trunc

        if truncated:
            self._log.warning(
                "command.output_truncated description=%r "
                "stdout=%d/%d stderr=%d/%d",
                description,
                len(stdout),
                spec.max_stdout_bytes,
                len(stderr),
                spec.max_stderr_bytes,
            )

        self._log.info(
            "command.executed description=%r returncode=%d elapsed=%.2fs",
            description,
            returncode,
            elapsed,
        )

        stdout_path, stderr_path = self._persist_logs(stdout, stderr)

        if truncated and strict_output:
            raise RunnerOutputTooLarge(
                f"command produced output larger than the configured cap "
                f"(stdout={len(stdout)}/{spec.max_stdout_bytes}, "
                f"stderr={len(stderr)}/{spec.max_stderr_bytes}): {spec.argv!r}"
            )

        return RunnerResult(
            command=CommandResult(
                argv=spec.argv,
                cwd=str(spec.cwd),
                returncode=returncode,
                elapsed_seconds=elapsed,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                env_summary=env_summary,
            ),
            executed=True,
            dry_run=False,
            stdout=stdout,
            stderr=stderr,
            output_truncated=truncated,
        )

    def _persist_logs(
        self, stdout: bytes, stderr: bytes
    ) -> tuple[str | None, str | None]:
        if self._log_dir is None:
            return None, None
        try:
            self._log_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self._log.warning(
                "command.log_dir_unavailable path=%s error=%s",
                self._log_dir,
                exc,
            )
            return None, None
        run_id = uuid.uuid4().hex
        out_path = self._log_dir / f"{run_id}.out"
        err_path = self._log_dir / f"{run_id}.err"
        try:
            out_path.write_bytes(stdout)
            err_path.write_bytes(stderr)
        except OSError as exc:
            self._log.warning(
                "command.log_write_failed dir=%s error=%s",
                self._log_dir,
                exc,
            )
            return None, None
        return str(out_path), str(err_path)


# ---------------------------------------------------------------------------
# FakeRunner
# ---------------------------------------------------------------------------


class FakeRunner:
    """Deterministic runner for tests. Implements :class:`RunnerProtocol`.

    Responses are popped from a FIFO queue. Each call to :meth:`run`
    records the ``(spec, dry_run)`` pair on :attr:`calls` so tests can assert
    what would have been executed.
    """

    def __init__(self, responses: Iterable[RunnerResult] | None = None) -> None:
        self._responses: list[RunnerResult] = list(responses or [])
        self._calls: list[tuple[CommandSpec, bool]] = []

    def run(
        self, spec: CommandSpec, *, dry_run: bool = False
    ) -> RunnerResult:
        self._calls.append((spec, dry_run))
        if not self._responses:
            raise RunnerError(
                f"FakeRunner: no queued response for argv={spec.argv!r}"
            )
        return self._responses.pop(0)

    def queue(self, result: RunnerResult) -> None:
        """Append a response to the queue."""
        self._responses.append(result)

    @property
    def calls(self) -> tuple[tuple[CommandSpec, bool], ...]:
        return tuple(self._calls)

    @property
    def remaining(self) -> int:
        return len(self._responses)
