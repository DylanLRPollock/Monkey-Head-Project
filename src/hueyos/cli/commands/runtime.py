"""Runtime command registration scaffold for incremental CLI extraction."""

from __future__ import annotations

import argparse
from typing import Callable


def _legacy_handler(name: str) -> Callable[[argparse.Namespace], int]:
    def _handler(args: argparse.Namespace) -> int:
        from huey.memory.PY import cli as legacy_cli

        return getattr(legacy_cli, name)(args)

    return _handler


def register_runtime_commands(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register runtime and utility commands via legacy handlers."""

    init_cmd = subparsers.add_parser(
        "init",
        help="Initialise the HueyOS workspace and memory directories.",
    )
    init_cmd.add_argument(
        "--verbose",
        action="store_true",
        help="Print the directories that were created during initialisation.",
    )
    init_cmd.add_argument(
        "--run-checks",
        action="store_true",
        help="Run system compatibility checks after creating directories.",
    )
    init_cmd.set_defaults(handler=_legacy_handler("_cmd_init"))

    run_cmd = subparsers.add_parser("run", help="Launch the HueyOS runtime.")
    run_cmd.add_argument("--cli", action="store_true", help="Launch the command line interface instead of the GUI.")
    run_cmd.add_argument("--gui", action="store_true", help="Explicitly launch the GUI even if other flags request CLI mode.")
    run_cmd.add_argument("--minimal", action="store_true", help="Use the lightweight CustomPyGPT CLI without GUI dependencies.")
    run_cmd.add_argument("--manager-ui", action="store_true", help="Launch the Tkinter program manager UI instead of the main runtime.")
    run_cmd.add_argument("--ml", action="store_true", help="Enable the ML optional dependency profile before launching.")
    run_cmd.add_argument("--cloud", action="store_true", help="Enable the cloud optional dependency profile before launching.")
    run_cmd.add_argument("--profile", action="append", default=[], help="Additional runtime profiles to export via HUEY_PROFILES.")
    run_cmd.add_argument("--skip-checks", action="store_true", help="Skip operating system and Python compatibility checks.")
    run_cmd.add_argument("--no-fallback", action="store_true", help="Do not fall back to the CLI if the GUI fails to launch.")
    run_cmd.set_defaults(handler=_legacy_handler("_cmd_run"))

    deploy_cmd = subparsers.add_parser("deploy", help="Deploy HueyOS services using Docker and/or Kubernetes.")
    deploy_cmd.add_argument("--mode", choices=["docker", "kubernetes", "all"], default="all", help="Select which deployment targets to execute.")
    deploy_cmd.add_argument("--compose-file", default="docker-compose.yml", help="Path to the Docker Compose file to apply.")
    deploy_cmd.add_argument("--manifest", default="k8s.yaml", help="Path to the Kubernetes manifest to apply.")
    deploy_cmd.add_argument("--dry-run", action="store_true", help="Print commands without executing them.")
    deploy_cmd.add_argument("--verbose", action="store_true", help="Show command output even when commands succeed.")
    deploy_cmd.set_defaults(handler=_legacy_handler("_cmd_deploy"))

    agent_cmd = subparsers.add_parser(
        "agent-status",
        help="Report scheduler task counts and recent resource observations.",
    )
    agent_cmd.add_argument("--json", action="store_true", help="Emit the status payload as JSON.")
    agent_cmd.add_argument("--verbose", action="store_true", help="Include details for each tracked task in the output.")
    agent_cmd.set_defaults(handler=_legacy_handler("_cmd_agent_status"))

    v1_run_cmd = subparsers.add_parser(
        "v1-run",
        help="Run the CI-safe V1 proof loop against an audio fixture.",
    )
    v1_run_cmd.add_argument("audio_file", help="Path to the audio fixture (for example fixture.mp3).")
    v1_run_cmd.add_argument(
        "--mock",
        action="store_true",
        help="Use fake transcription/cognition providers (CI-safe default path).",
    )
    v1_run_cmd.add_argument(
        "--log-dir",
        default=None,
        help="Directory for run artifacts. Defaults to ./runs.",
    )
    v1_run_cmd.set_defaults(handler=_legacy_handler("_cmd_v1_run"))

    v1_run_queue_cmd = subparsers.add_parser(
        "v1-run-queue",
        help="Run the CI-safe V1 proof loop across queued audio fixtures.",
    )
    v1_run_queue_cmd.add_argument(
        "--mock",
        action="store_true",
        help="Use fake transcription/cognition providers (CI-safe default path).",
    )
    v1_run_queue_cmd.add_argument(
        "--queue-dir",
        required=True,
        help="Directory containing queued fixtures.",
    )
    v1_run_queue_cmd.add_argument(
        "--log-dir",
        required=True,
        help="Directory for per-fixture structured logs.",
    )
    v1_run_queue_cmd.set_defaults(handler=_legacy_handler("_cmd_v1_run_queue"))
