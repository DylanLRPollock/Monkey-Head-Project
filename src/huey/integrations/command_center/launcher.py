"""Static metadata for the safe Windows HueyOS launcher."""

from __future__ import annotations

from pathlib import Path

LAUNCHER_VERSION = "0.2.0"
LAUNCHER_ASSET_DIR = (
    Path("src")
    / "huey"
    / "platform"
    / "installers"
    / "windows"
    / "launcher"
)
LAUNCHER_EXECUTABLE = LAUNCHER_ASSET_DIR / "HueyOS-Launcher-Setup.exe"
LAUNCHER_SOURCE = LAUNCHER_ASSET_DIR / "hueyos_launcher.go"


def _project_root() -> Path | None:
    current = Path(__file__).resolve()
    for candidate in current.parents:
        if (candidate / "pyproject.toml").is_file():
            return candidate
    cwd = Path.cwd()
    if (cwd / "pyproject.toml").is_file():
        return cwd
    return None


def _asset_details(project_root: Path | None, repo_path: Path) -> dict[str, object]:
    payload: dict[str, object] = {
        "repo_path": repo_path.as_posix(),
        "present": False,
    }
    if project_root is None:
        return payload

    absolute_path = project_root / repo_path
    payload["absolute_path"] = str(absolute_path)
    payload["present"] = absolute_path.is_file()
    return payload


def get_launcher_support() -> dict[str, object]:
    """Describe the safe Windows launcher bundled with the repository."""

    project_root = _project_root()
    return {
        "name": "HueyOS Launcher Setup",
        "version": LAUNCHER_VERSION,
        "platform": "windows",
        "mode": "safe-bootstrap",
        "launch_target": "HueyOS Command Center",
        "launch_entry_point": "huey.apps.command_center.cli --open",
        "asset_dir": LAUNCHER_ASSET_DIR.as_posix(),
        "assets": {
            "executable": _asset_details(project_root, LAUNCHER_EXECUTABLE),
            "source": _asset_details(project_root, LAUNCHER_SOURCE),
        },
        "config_paths": [
            r"%APPDATA%\HueyOS",
            r"%LOCALAPPDATA%\HueyOS",
            r"%LOCALAPPDATA%\HueyOS\logs",
            r"%LOCALAPPDATA%\HueyOS\workspace",
        ],
        "supported_commands": [
            {
                "option": "double-click",
                "usage": "Double-click",
                "behavior": (
                    "Creates HueyOS folders and config if needed, then tries to "
                    "launch HueyOS Command Center."
                ),
            },
            {
                "option": "--install",
                "usage": "HueyOS-Launcher-Setup.exe --install",
                "behavior": "Creates the HueyOS config, logs, and workspace folders.",
            },
            {
                "option": "--set-repo PATH",
                "usage": (
                    r"HueyOS-Launcher-Setup.exe --set-repo L:\Monkey-Head-Project"
                ),
                "behavior": "Saves the local Monkey-Head-Project checkout path.",
            },
            {
                "option": "--set-python PATH",
                "usage": (
                    r"HueyOS-Launcher-Setup.exe --set-python "
                    r"C:\Python313\python.exe"
                ),
                "behavior": "Pins a specific Python executable for launcher use.",
            },
            {
                "option": "--launch",
                "usage": "HueyOS-Launcher-Setup.exe --launch",
                "behavior": "Runs the configured HueyOS Command Center entry point.",
            },
            {
                "option": "--doctor",
                "usage": "HueyOS-Launcher-Setup.exe --doctor",
                "behavior": (
                    "Generates a local doctor report and opens it in Notepad."
                ),
            },
            {
                "option": "--open-config",
                "usage": "HueyOS-Launcher-Setup.exe --open-config",
                "behavior": "Opens the HueyOS config folder.",
            },
            {
                "option": "--help",
                "usage": "HueyOS-Launcher-Setup.exe --help",
                "behavior": "Shows launcher help.",
            },
        ],
        "doctor_checks": [
            "py",
            "python",
            "git",
            "ffmpeg",
            "ffprobe",
            "repo path",
            "pyproject.toml",
            "scripts/check_ffmpeg_environment.py",
            "scripts/prepare_audio_for_transcription.py",
        ],
        "safety_guarantees": [
            "No file deletion",
            "No Git mutation",
            "No firmware flashing",
            "No hardware control",
            "No robot/servo/power actions",
            "No arbitrary shell execution",
        ],
    }


__all__ = [
    "LAUNCHER_ASSET_DIR",
    "LAUNCHER_EXECUTABLE",
    "LAUNCHER_SOURCE",
    "LAUNCHER_VERSION",
    "get_launcher_support",
]
