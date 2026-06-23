"""Tests for the read-only GitHub dashboard client."""

from __future__ import annotations

import pytest

from huey.gui.github_client import GitHubReadOnlyClient, summarize_repo_status


def test_get_repo_rejects_list_payload(monkeypatch) -> None:
    client = GitHubReadOnlyClient()
    monkeypatch.setattr(client, "_request", lambda *args, **kwargs: [])

    with pytest.raises(TypeError, match="repository metadata"):
        client.get_repo("org/repo")


def test_summarize_repo_status_maps_known_repo_roles(monkeypatch) -> None:
    client = GitHubReadOnlyClient()

    monkeypatch.setattr(
        client,
        "get_repo",
        lambda full_name: {
            "default_branch": "main",
            "description": "dashboard repo",
            "html_url": f"https://github.com/{full_name}",
        },
    )
    monkeypatch.setattr(
        client,
        "list_workflow_runs",
        lambda full_name, branch=None: [{"conclusion": "success"}],
    )
    monkeypatch.setattr(
        client,
        "get_latest_commit",
        lambda full_name, branch="main": {"sha": "abcdef123456"},
    )
    monkeypatch.setattr(client, "list_pull_requests", lambda full_name: [{"number": 1}])
    monkeypatch.setattr(client, "list_issues", lambda full_name: [{"number": 2}])

    status = summarize_repo_status(client, "org/command-center")

    assert status.role == "dashboard"
    assert status.latest_workflow_status == "success"
    assert status.latest_commit == "abcdef1"
