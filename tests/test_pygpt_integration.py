from __future__ import annotations

import sys
from pathlib import Path

from huey.pygpt_integration import (
    candidate_src_paths,
    prepare_pygpt,
    reset_pygpt_state,
)


def test_candidate_src_paths_resolves_defaults_and_env(monkeypatch, tmp_path):
    root = Path(__file__).resolve().parents[1]
    extra_dir = tmp_path / "custom-src"
    extra_dir.mkdir()
    monkeypatch.setenv("PYGPT_EXTRA_PATHS", str(extra_dir))

    paths = candidate_src_paths()

    assert paths[0] == root / "pygpt"
    assert paths[1] == root / "pygpt" / "src"
    assert extra_dir in paths


def test_prepare_pygpt_uses_extra_paths(monkeypatch, tmp_path):
    dummy_root = tmp_path / "vendor"
    package_root = dummy_root / "pygpt_net"
    package_root.mkdir(parents=True)
    (package_root / "__init__.py").write_text("__version__ = 'test-vendor'\n")

    monkeypatch.setenv("PYGPT_EXTRA_PATHS", str(dummy_root))
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.delitem(sys.modules, "pygpt_net", raising=False)

    reset_pygpt_state()
    assert prepare_pygpt()

    import pygpt_net  # type: ignore

    assert getattr(pygpt_net, "__version__", None) == "test-vendor"
    reset_pygpt_state()
