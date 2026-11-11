"""Edge coverage for read-only GitHub and local bridge clients."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from huey.connectors.pyhuey.plugin.huey_tools.bridge import (
    HueyBridgeConfig,
    HueyToolBridge,
)
from huey.gui.github_client import (
    GitHubClientConfig,
    GitHubReadOnlyClient,
    client_from_env,
    summarize_repo_status,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.raised = False

    def raise_for_status(self):
        self.raised = True

    def json(self):
        return self.payload


def test_github_client_headers_timeout_and_request_params(monkeypatch) -> None:
    client = GitHubReadOnlyClient(
        GitHubClientConfig(token="secret", timeout_seconds=2.5, user_agent="tests")
    )
    response = FakeResponse([{"number": 2}])
    captured = {}

    def fake_get(url, **kwargs):
        captured.update(url=url, **kwargs)
        return response

    monkeypatch.setattr(client.session, "get", fake_get)
    assert client.list_pull_requests("org/repo", state="closed") == [{"number": 2}]
    assert response.raised is True
    assert client.session.headers["Authorization"] == "Bearer secret"
    assert client.session.headers["User-Agent"] == "tests"
    assert captured["url"] == "https://api.github.com/repos/org/repo/pulls"
    assert captured["params"] == {"state": "closed"}
    assert captured["timeout"] == 2.5


def test_github_client_filters_pull_requests_and_handles_empty_commit(monkeypatch) -> None:
    client = GitHubReadOnlyClient()
    payloads = iter([
        [{"number": 1}, {"number": 2, "pull_request": {"url": "api"}}, "bad"],
        [],
    ])
    monkeypatch.setattr(client, "_request", lambda *args, **kwargs: next(payloads))
    assert client.list_issues("org/repo") == [{"number": 1}]
    assert client.get_latest_commit("org/repo") == {}


@pytest.mark.parametrize(
    ("method", "payload", "message"),
    [
        ("list_pull_requests", {}, "pull requests"),
        ("list_issues", {}, "issues"),
        ("list_workflow_runs", [], "workflow runs"),
        ("get_latest_commit", {}, "commits"),
    ],
)
def test_github_client_rejects_wrong_payload_shapes(method, payload, message, monkeypatch):
    client = GitHubReadOnlyClient()
    monkeypatch.setattr(client, "_request", lambda *args, **kwargs: payload)
    with pytest.raises(TypeError, match=message):
        getattr(client, method)("org/repo")


def test_workflow_branch_is_optional_and_client_reads_environment(monkeypatch) -> None:
    client = GitHubReadOnlyClient()
    seen = []
    monkeypatch.setattr(client, "_request", lambda path, params=None: seen.append(params) or {"workflow_runs": []})
    assert client.list_workflow_runs("org/repo") == []
    assert client.list_workflow_runs("org/repo", branch="release") == []
    assert seen == [{"per_page": 10}, {"per_page": 10, "branch": "release"}]

    monkeypatch.setenv("GITHUB_TOKEN", "from-env")
    assert client_from_env().session.headers["Authorization"] == "Bearer from-env"
    monkeypatch.delenv("GITHUB_TOKEN")
    assert "Authorization" not in client_from_env().session.headers


def test_summarize_repo_status_uses_fallbacks_and_tooling_role(monkeypatch) -> None:
    client = GitHubReadOnlyClient()
    monkeypatch.setattr(client, "get_repo", lambda name: {})
    monkeypatch.setattr(client, "list_workflow_runs", lambda *a, **k: [{"status": "queued"}])
    monkeypatch.setattr(client, "get_latest_commit", lambda *a, **k: {})
    monkeypatch.setattr(client, "list_pull_requests", lambda name: [])
    monkeypatch.setattr(client, "list_issues", lambda name: [])
    status = summarize_repo_status(client, "org/unknown")
    assert status.role == "tooling"
    assert status.default_branch == "main"
    assert status.latest_workflow_status == "queued"
    assert status.latest_commit is None
    assert status.description == ""


def test_bridge_validates_roots_and_reports_optional_probe(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "project"
    project.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    bridge = HueyToolBridge(
        HueyBridgeConfig(
            monkey_head_project_path=project,
            allowed_workspace_roots=[workspace, workspace],
        )
    )
    assert bridge._allowed_roots() == [project.resolve(), workspace.resolve()]
    assert bridge._validate_user_path(workspace / "audio.wav", require_exists=False) == workspace / "audio.wav"
    with pytest.raises(ValueError, match="outside allowed workspaces"):
        bridge._validate_user_path(tmp_path / "outside.wav", require_exists=False)
    with pytest.raises(FileNotFoundError, match="Path does not exist"):
        bridge._validate_user_path(project / "missing.wav", require_exists=True)

    media = project / "clip.mp4"
    media.write_bytes(b"media")
    result = bridge.probe_media(media)
    assert result.returncode == 2
    assert result.ok is False
    assert "not available yet" in result.stderr


def test_bridge_external_paths_and_symlink_escape_are_explicit(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    bridge = HueyToolBridge(HueyBridgeConfig(monkey_head_project_path=project))
    with pytest.raises(ValueError, match="escapes project root"):
        bridge.script_path("../outside/file.py")
    link = project / "escape"
    link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="escapes project root"):
        bridge.script_path("escape/file.py")

    permissive = HueyToolBridge(
        HueyBridgeConfig(monkey_head_project_path=project, allow_external_paths=True)
    )
    assert permissive._validate_user_path(outside, require_exists=True) == outside


def test_bridge_module_timeout_and_result_serialization(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "project"
    project.mkdir()
    bridge = HueyToolBridge(
        HueyBridgeConfig(monkey_head_project_path=project, python_executable="python")
    )
    captured = {}

    def fake_run(command, **kwargs):
        captured.update(command=command, kwargs=kwargs)
        raise subprocess.TimeoutExpired(command, 0.25, output=b"partial")

    monkeypatch.setattr(
        "huey.connectors.pyhuey.plugin.huey_tools.bridge.subprocess.run", fake_run
    )
    result = bridge.run_module("huey.cli", ["--help"], timeout_seconds=0.25)
    assert captured["command"] == ["python", "-m", "huey.cli", "--help"]
    assert captured["kwargs"]["shell"] is False
    assert result.stdout == "partial"
    assert result.returncode == 124
    assert result.to_dict()["cwd"] == str(project)


@pytest.mark.parametrize("stdout", ["", "plain output", "null", "42", "{broken", "[broken"])
def test_bridge_json_parser_returns_none_for_non_json_or_invalid(stdout: str) -> None:
    assert HueyToolBridge._parse_json(stdout) is None


def test_bridge_parses_json_list_and_nonzero_exit(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "project"
    project.mkdir()
    script = project / "scripts" / "tool.py"
    script.parent.mkdir()
    script.write_text("pass\n", encoding="utf-8")

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 7, stdout="[1, 2]", stderr="failed")

    monkeypatch.setattr(
        "huey.connectors.pyhuey.plugin.huey_tools.bridge.subprocess.run", fake_run
    )
    result = HueyToolBridge(HueyBridgeConfig(monkey_head_project_path=project)).run_script(
        "scripts/tool.py", []
    )
    assert result.ok is False
    assert result.parsed_json == [1, 2]
    assert result.stderr == "failed"
