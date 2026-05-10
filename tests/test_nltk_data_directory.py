"""Tests ensuring NLTK data is stored in a private directory."""

from __future__ import annotations

import importlib
import os
import sys

from huey.pyhuey_integration import prepare_pygpt, reset_pygpt_state


def test_nltk_data_directory_is_user_specific(monkeypatch, tmp_path) -> None:
    """NLTK data should default to a private per-user directory."""

    monkeypatch.delenv("NLTK_DATA", raising=False)
    custom_dir = tmp_path / "secure-nltk"
    monkeypatch.setenv("PYGPT_NLTK_DATA_DIR", str(custom_dir))
    monkeypatch.delitem(sys.modules, "pygpt_net", raising=False)

    reset_pygpt_state()
    assert prepare_pygpt(source="package")

    module = importlib.import_module("pygpt_net")
    try:
        importlib.reload(module)
    finally:
        # Ensure future imports see the original module object.
        sys.modules["pygpt_net"] = module

    assert os.environ.get("NLTK_DATA") == str(custom_dir)
    assert custom_dir.exists()
    assert custom_dir.is_dir()
