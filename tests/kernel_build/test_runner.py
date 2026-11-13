"""Tests for huey.kernel_build.runner (Step 6; Step 35 expands).

All tests run offline on any Python 3.13 interpreter. Real-subprocess tests
use ``sys.executable`` with ``python -c`` for portability, and never invoke
a shell.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from huey.kernel_build.models import CommandResult
from huey.kernel_build.runner import (
    DRY_RUN_RETURNCODE,
    CommandSpec,
    FakeRunner,
    Runner,
    RunnerError,
    RunnerOutputTooLarge,
    RunnerResult,
    RunnerTimeout,
    is_dry_run,
)

PYTHON = sys.executable


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_spec(*argv: str, cwd: Path, **kwargs) -> CommandSpec:
    return CommandSpec(argv=tuple(argv), cwd=cwd, **kwargs)


def _py(script: str) -> tuple[str, str, str]:
    return (PYTHON, "-c", script)


def _fake_result(
    argv: tuple[str, ...],
    *,
    returncode: int = 0,
    stdout: bytes = b"",
    stderr: bytes = b"",
    cwd: str = "/tmp",
    executed: bool = True,
    dry_run: bool = False,
    truncated: bool = False,
) -> RunnerResult:
    return RunnerResult(
        command=CommandResult(
            argv=argv,
            cwd=cwd,
            returncode=returncode,
            elapsed_seconds=0.01,
        ),
        executed=executed,
        dry_run=dry_run,
        stdout=stdout,
        stderr=stderr,
        output_truncated=truncated,
    )


# ---------------------------------------------------------------------------
# CommandSpec validation
# ---------------------------------------------------------------------------


def test_spec_rejects_empty_argv(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="non-empty"):
        CommandSpec(argv=(), cwd=tmp_path)


def test_spec_rejects_empty_string_in_argv(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="empty strings"):
        CommandSpec(argv=("echo", ""), cwd=tmp_path)


def test_spec_accepts_list_argv(tmp_path: Path) -> None:
    spec = CommandSpec(argv=["echo", "hi"], cwd=tmp_path)  # type: ignore[arg-type]
    assert spec.argv == ("echo", "hi")


def test_spec_accepts_str_cwd(tmp_path: Path) -> None:
    spec = CommandSpec(argv=("echo",), cwd=str(tmp_path))  # type: ignore[arg-type]
    assert spec.cwd == tmp_path


def test_spec_rejects_zero_timeout(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="timeout"):
        CommandSpec(argv=("echo",), cwd=tmp_path, timeout_seconds=0)


def test_spec_rejects_negative_output_limit(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="max_stdout_bytes"):
        CommandSpec(argv=("echo",), cwd=tmp_path, max_stdout_bytes=0)


def test_spec_rejects_non_str_env_value(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match="str"):
        CommandSpec(
            argv=("echo",),
            cwd=tmp_path,
            env_overrides={"X": 1},  # type: ignore[dict-item]
        )


# ---------------------------------------------------------------------------
# Dry run
# ---------------------------------------------------------------------------


def test_dry_run_does_not_execute(tmp_path: Path) -> None:
    """A nonexistent binary must not raise: dry run never launches anything."""
    spec = _make_spec(
        "huey-this-binary-does-not-exist-xyz", cwd=tmp_path
    )
    result = Runner().run(spec, dry_run=True)
    assert result.executed is False
    assert result.dry_run is True
    assert result.command.returncode == DRY_RUN_RETURNCODE
    assert is_dry_run(result.command) is True
    assert result.stdout is None
    assert result.stderr is None
    assert result.succeeded is False


def test_dry_run_records_argv_and_cwd(tmp_path: Path) -> None:
    spec = _make_spec(
        "make", "-j4", "bindeb-pkg", cwd=tmp_path, description="kernel build"
    )
    result = Runner().run(spec, dry_run=True)
    assert result.command.argv == ("make", "-j4", "bindeb-pkg")
    assert result.command.cwd == str(tmp_path)
    assert result.command.elapsed_seconds == 0.0


def test_dry_run_does_not_validate_cwd(tmp_path: Path) -> None:
    """Planning does not require the cwd to exist yet."""
    spec = _make_spec(
        "make", cwd=tmp_path / "not-yet-created"
    )
    result = Runner().run(spec, dry_run=True)
    assert result.dry_run is True


def test_dry_run_redacts_env_secrets(tmp_path: Path) -> None:
    spec = _make_spec(
        *(_py("pass")),
        cwd=tmp_path,
        env_overrides={"MY_TOKEN": "abc", "PUBLIC_VAR": "ok"},
    )
    result = Runner().run(spec, dry_run=True)
    assert result.command.env_summary["MY_TOKEN"] == "<redacted>"
    assert result.command.env_summary["PUBLIC_VAR"] == "ok"


# ---------------------------------------------------------------------------
# Real execution: success and exit codes
# ---------------------------------------------------------------------------


def test_real_run_captures_stdout(tmp_path: Path) -> None:
    spec = _make_spec(*_py("print('hello')"), cwd=tmp_path)
    result = Runner().run(spec)
    assert result.executed is True
    assert result.dry_run is False
    assert result.command.returncode == 0
    assert result.stdout == b"hello\n"
    assert result.succeeded is True


def test_real_run_captures_stderr(tmp_path: Path) -> None:
    spec = _make_spec(
        *_py("import sys; sys.stderr.write('oops\\n')"), cwd=tmp_path
    )
    result = Runner().run(spec)
    assert result.stderr == b"oops\n"


def test_nonzero_exit_is_returned_not_raised(tmp_path: Path) -> None:
    spec = _make_spec(*_py("import sys; sys.exit(3)"), cwd=tmp_path)
    result = Runner().run(spec)
    assert result.executed is True
    assert result.command.returncode == 3
    assert result.succeeded is False


def test_real_run_records_elapsed(tmp_path: Path) -> None:
    spec = _make_spec(*_py("pass"), cwd=tmp_path)
    result = Runner().run(spec)
    assert result.command.elapsed_seconds >= 0.0


# ---------------------------------------------------------------------------
# Shell metacharacter inertness
# ---------------------------------------------------------------------------


def test_shell_metacharacters_are_inert(tmp_path: Path) -> None:
    """Metacharacters inside an argv element must not be interpreted."""
    marker = tmp_path / "should-not-exist"
    payload = f"a b ; touch {marker} ; echo done"
    spec = _make_spec(
        PYTHON,
        "-c",
        "import sys; print(sys.argv[1])",
        payload,
        cwd=tmp_path,
    )
    result = Runner().run(spec)
    assert result.command.returncode == 0
    assert not marker.exists(), (
        f"payload was interpreted by a shell: {payload!r}"
    )
    assert payload.encode() in (result.stdout or b"")


def test_spaces_in_argv_preserved(tmp_path: Path) -> None:
    spec = _make_spec(
        PYTHON,
        "-c",
        "import sys; print(repr(sys.argv[1]))",
        "two  spaces",
        cwd=tmp_path,
    )
    result = Runner().run(spec)
    assert b"'two  spaces'" in (result.stdout or b"")


# ---------------------------------------------------------------------------
# Failure modes
# ---------------------------------------------------------------------------


def test_missing_executable_raises_runner_error(tmp_path: Path) -> None:
    spec = _make_spec(
        "huey-this-binary-definitely-not-real-xyz", cwd=tmp_path
    )
    with pytest.raises(RunnerError, match="executable not found"):
        Runner().run(spec)


def test_cwd_must_exist_for_real_run(tmp_path: Path) -> None:
    spec = _make_spec(*_py("pass"), cwd=tmp_path / "does-not-exist")
    with pytest.raises(RunnerError, match="cwd"):
        Runner().run(spec)


def test_timeout_raises_runner_timeout(tmp_path: Path) -> None:
    spec = _make_spec(
        *_py("import time; time.sleep(10)"),
        cwd=tmp_path,
        timeout_seconds=0.4,
    )
    with pytest.raises(RunnerTimeout):
        Runner().run(spec)


# ---------------------------------------------------------------------------
# Output truncation
# ---------------------------------------------------------------------------


def test_output_truncation_is_flagged(tmp_path: Path) -> None:
    spec = _make_spec(
        *_py("print('x' * 1000)"),
        cwd=tmp_path,
        max_stdout_bytes=100,
    )
    result = Runner().run(spec)
    assert result.output_truncated is True
    assert len(result.stdout or b"") == 100
    assert result.succeeded is False


def test_output_truncation_raises_in_strict_mode(tmp_path: Path) -> None:
    spec = _make_spec(
        *_py("print('x' * 1000)"),
        cwd=tmp_path,
        max_stdout_bytes=100,
    )
    with pytest.raises(RunnerOutputTooLarge):
        Runner().run(spec, strict_output=True)


# ---------------------------------------------------------------------------
# Log persistence
# ---------------------------------------------------------------------------


def test_log_dir_persists_stdout_stderr(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    runner = Runner(log_dir=log_dir)
    spec = _make_spec(*_py("print('hi')"), cwd=tmp_path)
    result = runner.run(spec)
    assert result.command.stdout_path is not None
    assert result.command.stderr_path is not None
    assert Path(result.command.stdout_path).read_bytes() == b"hi\n"
    assert Path(result.command.stderr_path).read_bytes() == b""


def test_no_log_dir_leaves_paths_none(tmp_path: Path) -> None:
    spec = _make_spec(*_py("print('hi')"), cwd=tmp_path)
    result = Runner().run(spec)
    assert result.command.stdout_path is None
    assert result.command.stderr_path is None


# ---------------------------------------------------------------------------
# FakeRunner
# ---------------------------------------------------------------------------


def test_fake_runner_returns_queued_result(tmp_path: Path) -> None:
    spec = _make_spec("echo", "hi", cwd=tmp_path)
    expected = _fake_result(("echo", "hi"), stdout=b"hi\n", cwd=str(tmp_path))
    fake = FakeRunner([expected])
    got = fake.run(spec)
    assert got is expected
    assert len(fake.calls) == 1
    assert fake.calls[0][0] is spec
    assert fake.calls[0][1] is False
    assert fake.remaining == 0


def test_fake_runner_raises_when_empty(tmp_path: Path) -> None:
    spec = _make_spec("echo", "hi", cwd=tmp_path)
    with pytest.raises(RunnerError, match="no queued response"):
        FakeRunner().run(spec)


def test_fake_runner_records_dry_run_flag(tmp_path: Path) -> None:
    spec = _make_spec("echo", "hi", cwd=tmp_path)
    fake = FakeRunner(
        [_fake_result(("echo",), executed=False, dry_run=True)]
    )
    fake.run(spec, dry_run=True)
    assert fake.calls[0][1] is True


# ---------------------------------------------------------------------------
# RunnerResult.succeeded
# ---------------------------------------------------------------------------


def test_succeeded_property_reflects_state() -> None:
    ok = _fake_result(("a",), returncode=0)
    assert ok.succeeded is True

    failed = _fake_result(("a",), returncode=1)
    assert failed.succeeded is False

    dry = _fake_result(
        ("a",),
        returncode=DRY_RUN_RETURNCODE,
        executed=False,
        dry_run=True,
    )
    assert dry.succeeded is False

    truncated = _fake_result(("a",), returncode=0, truncated=True)
    assert truncated.succeeded is False
