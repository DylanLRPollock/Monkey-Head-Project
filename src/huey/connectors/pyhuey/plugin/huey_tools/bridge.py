"""Safe bridge for invoking fixed Monkey-Head-Project commands."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class HueyBridgeConfig:
    monkey_head_project_path: Path | None
    python_executable: Path | str = sys.executable
    timeout_seconds: float = 120.0
    allow_external_paths: bool = False
    allowed_workspace_roots: list[Path] = field(default_factory=list)


@dataclass(slots=True)
class HueyBridgeResult:
    command: list[str]
    cwd: Path | None
    returncode: int
    stdout: str
    stderr: str
    parsed_json: dict | list | None = None
    ok: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "command": list(self.command),
            "cwd": None if self.cwd is None else str(self.cwd),
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "parsed_json": self.parsed_json,
            "ok": self.ok,
        }


class HueyToolBridge:
    """Bridge fixed commands into the local Monkey-Head-Project checkout."""

    def __init__(self, config: HueyBridgeConfig | None = None) -> None:
        self.config = config or HueyBridgeConfig(monkey_head_project_path=None)

    def status(self) -> dict[str, object]:
        project_path = self.config.monkey_head_project_path
        project_exists = project_path.exists() if project_path is not None else False
        return {
            "project_path": None if project_path is None else str(project_path),
            "project_path_exists": project_exists,
            "python_executable": str(self.config.python_executable),
            "timeout_seconds": self.config.timeout_seconds,
            "allow_external_paths": self.config.allow_external_paths,
            "allowed_workspace_roots": [
                str(path) for path in self._allowed_roots(include_project=False)
            ],
            "available_scripts": self.list_available_scripts(),
        }

    def resolve_project_path(self) -> Path:
        project_path = self.config.monkey_head_project_path
        if project_path is None:
            raise RuntimeError("Monkey-Head-Project path is not configured")
        resolved = project_path.expanduser().resolve()
        if not resolved.exists():
            raise RuntimeError(f"Monkey-Head-Project path does not exist: {resolved}")
        return resolved

    def script_path(self, relative_path: str) -> Path:
        project_root = self.resolve_project_path()
        candidate = (project_root / relative_path).resolve()
        if project_root not in candidate.parents and candidate != project_root:
            raise ValueError(f"Script path escapes project root: {relative_path}")
        return candidate

    def run_script(
        self,
        relative_script: str,
        args: list[str],
        timeout_seconds: float | None = None,
    ) -> HueyBridgeResult:
        script = self.script_path(relative_script)
        if not script.exists():
            raise FileNotFoundError(f"Script not found: {script}")
        command = [str(self.config.python_executable), str(script), *args]
        return self._run(command, cwd=self.resolve_project_path(), timeout_seconds=timeout_seconds)

    def run_module(
        self,
        module: str,
        args: list[str],
        timeout_seconds: float | None = None,
    ) -> HueyBridgeResult:
        command = [str(self.config.python_executable), "-m", module, *args]
        return self._run(command, cwd=self.resolve_project_path(), timeout_seconds=timeout_seconds)

    def check_ffmpeg(self, strict: bool = False) -> HueyBridgeResult:
        args = ["--json"]
        if strict:
            args.append("--strict")
        return self.run_script("scripts/check_ffmpeg_environment.py", args)

    def prepare_audio(
        self,
        source_path: str | Path,
        output_path: str | Path | None = None,
        overwrite: bool = False,
    ) -> HueyBridgeResult:
        self.resolve_project_path()
        source = self._validate_user_path(source_path, require_exists=True)
        args = [str(source), "--json"]
        if output_path is not None:
            output = self._validate_user_path(output_path, require_exists=False)
            args.extend(["--output", str(output)])
        if overwrite:
            args.append("--overwrite")
        return self.run_script("scripts/prepare_audio_for_transcription.py", args)

    def probe_media(self, path: str | Path) -> HueyBridgeResult:
        self.resolve_project_path()
        source = self._validate_user_path(path, require_exists=True)
        scripts = self.list_available_scripts()
        if not scripts.get("probe_media", False):
            return HueyBridgeResult(
                command=["scripts/probe_media.py", str(source)],
                cwd=self.config.monkey_head_project_path,
                returncode=2,
                stdout="",
                stderr=(
                    "Media probe CLI is not available yet. Implement a probe wrapper "
                    "in Monkey-Head-Project first."
                ),
                ok=False,
            )
        return self.run_script("scripts/probe_media.py", [str(source), "--json"])

    def list_available_scripts(self) -> dict[str, bool]:
        try:
            project_root = self.resolve_project_path()
        except RuntimeError:
            return {
                "check_ffmpeg_environment": False,
                "prepare_audio_for_transcription": False,
                "probe_media": False,
            }
        return {
            "check_ffmpeg_environment": (project_root / "scripts" / "check_ffmpeg_environment.py").exists(),
            "prepare_audio_for_transcription": (
                project_root / "scripts" / "prepare_audio_for_transcription.py"
            ).exists(),
            "probe_media": (project_root / "scripts" / "probe_media.py").exists(),
        }

    def _allowed_roots(self, *, include_project: bool = True) -> list[Path]:
        roots = [
            path.expanduser().resolve()
            for path in self.config.allowed_workspace_roots
        ]
        if include_project and self.config.monkey_head_project_path is not None:
            roots.insert(0, self.config.monkey_head_project_path.expanduser().resolve())
        unique: list[Path] = []
        for path in roots:
            if path not in unique:
                unique.append(path)
        return unique

    def _validate_user_path(
        self, path: str | Path, *, require_exists: bool
    ) -> Path:
        resolved = Path(path).expanduser().resolve()
        if require_exists and not resolved.exists():
            raise FileNotFoundError(f"Path does not exist: {resolved}")
        if self.config.allow_external_paths:
            return resolved
        if not any(
            root == resolved or root in resolved.parents for root in self._allowed_roots()
        ):
            raise ValueError(f"Path is outside allowed workspaces: {resolved}")
        return resolved

    def _run(
        self,
        command: list[str],
        *,
        cwd: Path | None,
        timeout_seconds: float | None = None,
    ) -> HueyBridgeResult:
        timeout = self.config.timeout_seconds if timeout_seconds is None else timeout_seconds
        try:
            completed = subprocess.run(
                command,
                cwd=None if cwd is None else str(cwd),
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return HueyBridgeResult(
                command=command,
                cwd=cwd,
                returncode=124,
                stdout=self._coerce_text(exc.stdout),
                stderr=f"Command timed out after {timeout} seconds",
                ok=False,
            )
        result = HueyBridgeResult(
            command=command,
            cwd=cwd,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            ok=completed.returncode == 0,
        )
        result.parsed_json = self._parse_json(result.stdout)
        return result

    @staticmethod
    def _coerce_text(value: str | bytes | None) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return value

    @staticmethod
    def _parse_json(stdout: str) -> dict | list | None:
        text = stdout.strip()
        if not text.startswith("{") and not text.startswith("["):
            return None
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, (dict, list)):
            return parsed
        return None


__all__ = ["HueyBridgeConfig", "HueyBridgeResult", "HueyToolBridge"]
