"""Tests for the Command Center browser launcher helpers."""

from __future__ import annotations

from pathlib import Path

from huey.apps.command_center import cli


def test_local_frontend_path_detects_bundled_dist(tmp_path: Path) -> None:
    dist = tmp_path / "integrations" / "command-center" / "dist"
    dist.mkdir(parents=True)
    index = dist / "index.html"
    index.write_text("<html></html>", encoding="utf-8")

    assert cli.local_frontend_path(tmp_path) == index
    assert cli.resolve_frontend_url(tmp_path) == index.resolve().as_uri()


def test_resolve_frontend_url_prefers_configured_env(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("HUEY_COMMAND_CENTER_FRONTEND", "https://example.invalid/ui")
    dist = tmp_path / "integrations" / "command-center" / "dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text("<html></html>", encoding="utf-8")

    assert cli.resolve_frontend_url(tmp_path) == "https://example.invalid/ui"


def test_open_command_center_uses_resolved_url(monkeypatch) -> None:
    monkeypatch.setattr(
        cli, "resolve_frontend_url", lambda project_root=None: "file:///tmp/index.html"
    )
    opened: dict[str, str] = {}
    monkeypatch.setattr(cli, "open_browser", lambda url: opened.setdefault("url", url))

    assert cli.open_command_center() == "file:///tmp/index.html"
    assert opened["url"] == "file:///tmp/index.html"
