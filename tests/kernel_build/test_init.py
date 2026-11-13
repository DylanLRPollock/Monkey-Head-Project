"""Tests for the huey.kernel_build package init (Step 3).

The handoff requires that importing the package performs no work: no
subprocess is launched, no files are touched, and no optional third-party
modules are eagerly imported. These tests run in isolated subprocess
interpreters so that whatever pytest or the parent test session has already
imported cannot mask an accidental eager import in the package.

Full schema and policy validation lives in Step 4 / Step 33 and Step 5 /
Step 34. This file only guards the package-init contract.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"

# Modules that the package init must never eagerly load. ``yaml`` is the
# explicit concern from the handoff (it is added lazily in later steps);
# the ML stacks below would indicate accidental coupling and are checked as
# well. Any module that a caller's interpreter already had loaded is
# subtracted, so these tests measure *this* package's import side effects.
_EAGER_FORBIDDEN_MODULES = ("yaml", "numpy", "torch", "tensorflow")


def _subprocess_env() -> dict[str, str]:
    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(SRC_DIR) + (os.pathsep + existing if existing else "")
    return env


def _run_python(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env=_subprocess_env(),
        timeout=60,
        check=False,
    )


def test_import_succeeds_in_process() -> None:
    """The package imports and exposes a non-empty ``__version__`` string."""
    import huey.kernel_build as pkg

    assert isinstance(pkg.__version__, str)
    assert pkg.__version__


def test_all_is_a_sequence_of_strings() -> None:
    """``__all__`` is defined and contains only strings."""
    import huey.kernel_build as pkg

    assert isinstance(pkg.__all__, (list, tuple))
    assert all(isinstance(name, str) for name in pkg.__all__)


def test_import_in_clean_subprocess_emits_no_stdout_or_stderr() -> None:
    """A clean ``python -c 'import huey.kernel_build'`` exits 0 with no output."""
    proc = _run_python("import huey.kernel_build")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == "", f"import produced stdout: {proc.stdout!r}"
    assert proc.stderr == "", f"import produced stderr: {proc.stderr!r}"


@pytest.mark.parametrize("module_name", _EAGER_FORBIDDEN_MODULES)
def test_optional_dependencies_not_imported_eagerly(module_name: str) -> None:
    """Importing the package must not transitively import heavy/optional modules.

    The check subtracts whatever the interpreter already had loaded, so it
    measures only the modules brought in by ``import huey.kernel_build``
    itself, not by site initialization or pytest.
    """
    code = (
        "import sys\n"
        "before = set(sys.modules)\n"
        "import huey.kernel_build\n"
        "new = set(sys.modules) - before\n"
        f"print({module_name!r} in new)\n"
    )
    proc = _run_python(code)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "False", (
        f"importing huey.kernel_build eagerly loaded {module_name!r}:\n"
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
