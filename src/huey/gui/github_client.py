"""Read-only GitHub API helpers for dashboard and operator surfaces."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TypeIs

import requests

from huey.gui.models import RepoRole, RepoStatus

type GitHubRecord = dict[str, object]
type GitHubCollection = list[GitHubRecord]


def _is_github_record(payload: GitHubRecord | GitHubCollection) -> TypeIs[GitHubRecord]:
    return isinstance(payload, dict)


def _is_github_collection(
    payload: GitHubRecord | GitHubCollection,
) -> TypeIs[GitHubCollection]:
    return isinstance(payload, list)


@dataclass(frozen=True)
class GitHubClientConfig:
    token: str | None = None
    timeout_seconds: float = 10.0
    user_agent: str = "HueyOS-Command-Center"


class GitHubReadOnlyClient:
    """Small read-only client for repository status surfaces."""

    base_url = "https://api.github.com"

    def __init__(self, config: GitHubClientConfig | None = None) -> None:
        self.config = config or GitHubClientConfig()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "User-Agent": self.config.user_agent,
            }
        )
        if self.config.token:
            self.session.headers["Authorization"] = f"Bearer {self.config.token}"

    def get_repo(self, full_name: str) -> GitHubRecord:
        """Fetch public repository metadata."""

        payload = self._request(f"/repos/{full_name}")
        if not _is_github_record(payload):
            raise TypeError(
                "Expected GitHub API object payload for repository metadata"
            )
        return payload

    def list_pull_requests(
        self, full_name: str, state: str = "open"
    ) -> GitHubCollection:
        """Fetch PR metadata."""

        payload = self._request(f"/repos/{full_name}/pulls", params={"state": state})
        if not _is_github_collection(payload):
            raise TypeError("Expected GitHub API list payload for pull requests")
        return list(payload)

    def list_issues(self, full_name: str, state: str = "open") -> GitHubCollection:
        """Fetch issues excluding pull requests."""

        payload = self._request(f"/repos/{full_name}/issues", params={"state": state})
        if not _is_github_collection(payload):
            raise TypeError("Expected GitHub API list payload for issues")
        return [
            item
            for item in payload
            if isinstance(item, dict) and "pull_request" not in item
        ]

    def list_workflow_runs(
        self, full_name: str, branch: str | None = None
    ) -> GitHubCollection:
        """Fetch recent workflow run metadata."""

        params = {"per_page": 10}
        if branch:
            params["branch"] = branch
        payload = self._request(
            f"/repos/{full_name}/actions/runs",
            params=params,
        )
        if not _is_github_record(payload):
            raise TypeError("Expected GitHub API object payload for workflow runs")
        return list(payload.get("workflow_runs", []))

    def get_latest_commit(self, full_name: str, branch: str = "main") -> GitHubRecord:
        """Fetch the latest commit on a branch."""

        payload = self._request(
            f"/repos/{full_name}/commits",
            params={"sha": branch, "per_page": 1},
        )
        if not _is_github_collection(payload):
            raise TypeError("Expected GitHub API list payload for commits")
        if not payload:
            return {}
        return dict(payload[0])

    def _request(
        self, path: str, params: dict[str, object] | None = None
    ) -> GitHubRecord | GitHubCollection:
        response = self.session.get(
            f"{self.base_url}{path}",
            params=params,
            timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()


def client_from_env() -> GitHubReadOnlyClient:
    """Build a client using the optional ``GITHUB_TOKEN`` environment variable."""

    return GitHubReadOnlyClient(
        GitHubClientConfig(token=os.environ.get("GITHUB_TOKEN") or None)
    )


def summarize_repo_status(client: GitHubReadOnlyClient, full_name: str) -> RepoStatus:
    """Convert GitHub API data into a ``RepoStatus`` record."""

    repo = client.get_repo(full_name)
    default_branch = str(repo.get("default_branch", "main"))
    workflows = client.list_workflow_runs(full_name, branch=default_branch)
    commit = client.get_latest_commit(full_name, branch=default_branch)
    repo_name = full_name.rsplit("/", 1)[-1]
    role_map: dict[str, RepoRole] = {
        "Monkey-Head-Project": "runtime",
        "PyHuey": "cockpit",
        "command-center": "dashboard",
        "dlrp.ca": "website",
    }
    role: RepoRole = role_map.get(repo_name, "tooling")
    latest_workflow = workflows[0] if workflows else {}
    return RepoStatus(
        name=repo_name,
        full_name=full_name,
        role=role,
        description=str(repo.get("description") or ""),
        default_branch=default_branch,
        url=str(repo.get("html_url") or ""),
        open_prs=len(client.list_pull_requests(full_name)),
        open_issues=len(client.list_issues(full_name)),
        latest_workflow_status=str(
            latest_workflow.get("conclusion") or latest_workflow.get("status") or ""
        )
        or None,
        latest_commit=str(commit.get("sha", ""))[:7] or None,
        data_mode="live",
    )


__all__ = [
    "GitHubClientConfig",
    "GitHubReadOnlyClient",
    "client_from_env",
    "summarize_repo_status",
]
