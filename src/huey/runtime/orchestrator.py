"""Master runtime coordinator for HueyOS subsystem integration."""

from __future__ import annotations

import importlib.util
from typing import Callable

from huey.media.ffmpeg_validator import validate_media_environment
from huey.runtime.dependency_graph import DependencyGraph
from huey.runtime.service_registry import ServiceRecord, ServiceRegistry
from huey.utils.paths import get_memory_path

HealthPayload = dict[str, object] | bool | str | None


class RuntimeOrchestrator:
    """Coordinate subsystem registration, dependency order, and health state."""

    def __init__(self, *, bootstrap_defaults: bool = True) -> None:
        self.registry = ServiceRegistry()
        self.dependency_graph = DependencyGraph()
        self.pipelines: dict[str, dict[str, object]] = {}
        self.models: dict[str, dict[str, object]] = {}
        self._started = False
        if bootstrap_defaults:
            self._bootstrap_defaults()

    def register_service(
        self,
        name: str,
        description: str,
        *,
        dependencies: list[str] | tuple[str, ...] = (),
        status: str = "unknown",
        metadata: dict[str, object] | None = None,
        healthcheck: Callable[[], HealthPayload] | None = None,
    ) -> ServiceRecord:
        record = self.registry.register_service(
            name,
            description,
            dependencies=dependencies,
            status=status,
            metadata=metadata,
            healthcheck=healthcheck,
        )
        self.dependency_graph.register(name, list(dependencies))
        return record

    def register_pipeline(
        self,
        name: str,
        *,
        description: str,
        steps: list[str],
        metadata: dict[str, object] | None = None,
    ) -> dict[str, object]:
        payload = {
            "name": name,
            "description": description,
            "steps": list(steps),
            "metadata": dict(metadata or {}),
        }
        self.pipelines[name] = payload
        return payload

    def register_model(
        self,
        name: str,
        *,
        provider: str,
        metadata: dict[str, object] | None = None,
    ) -> dict[str, object]:
        payload = {
            "name": name,
            "provider": provider,
            "metadata": dict(metadata or {}),
        }
        self.models[name] = payload
        return payload

    def start(self) -> dict[str, object]:
        """Mark the orchestrator active and return the planned startup order."""

        self._started = True
        order = self.dependency_graph.startup_order()
        for service_name in order:
            record = self.registry.get(service_name)
            if record.status in {"unknown", "stopped"}:
                record.status = "ready"
        return {"started": True, "startup_order": order}

    def stop(self) -> dict[str, object]:
        """Mark the orchestrator stopped."""

        self._started = False
        for record in self.registry.all():
            if record.status != "blocked":
                record.status = "stopped"
        return {"started": False}

    def restart(self) -> dict[str, object]:
        """Restart orchestration state."""

        self.stop()
        return self.start()

    def health_check(self) -> dict[str, dict[str, object]]:
        """Run service health checks and update registry state."""

        results: dict[str, dict[str, object]] = {}
        for record in self.registry.all():
            payload = self._run_healthcheck(record)
            results[record.name] = payload
        return results

    def status(self) -> dict[str, object]:
        """Return a serializable runtime status snapshot."""

        return {
            "started": self._started,
            "startup_order": self.dependency_graph.startup_order(),
            "services": self.registry.as_dict(),
            "pipelines": dict(self.pipelines),
            "models": dict(self.models),
            "dependencies": self.dependency_graph.as_dict(),
        }

    def _bootstrap_defaults(self) -> None:
        self.register_service(
            "memory",
            "Shared memory workspace and ingestable storage tree.",
            healthcheck=lambda: {
                "ready": get_memory_path(create=True).exists(),
                "path": str(get_memory_path(create=True)),
            },
        )
        self.register_service(
            "ffmpeg",
            "FFmpeg and ffprobe media processing toolchain.",
            healthcheck=validate_media_environment,
        )
        self.register_service(
            "transcription",
            "Speech pipeline and Whisper-compatible transcription stack.",
            dependencies=("ffmpeg",),
            healthcheck=lambda: {
                "ready": importlib.util.find_spec("faster_whisper") is not None,
                "module": "faster_whisper",
            },
        )
        self.register_service(
            "api",
            "HueyOS API health surface.",
            dependencies=("memory",),
            healthcheck=self._check_api,
        )
        self.register_service(
            "command_center",
            "Read-only local backend for the external Command Center frontend.",
            dependencies=("api",),
            healthcheck=self._check_command_center,
        )
        self.register_service(
            "pyhuey",
            "PyHuey cockpit integration adapter.",
            dependencies=("api",),
            healthcheck=self._check_pyhuey,
        )
        self.register_service(
            "ollama",
            "Optional local model provider.",
            healthcheck=lambda: {
                "ready": importlib.util.find_spec("ollama") is not None,
                "module": "ollama",
            },
        )
        self.register_pipeline(
            "v1-proof-loop",
            description=(
                "Controlled MP3 fixture -> transcription -> cognition -> "
                "structured log."
            ),
            steps=[
                "prepare-media",
                "transcribe-fixture",
                "generate-response",
                "write-run-record",
            ],
        )
        self.register_model(
            "default-ollama",
            provider="ollama",
            metadata={"available": importlib.util.find_spec("ollama") is not None},
        )

    @staticmethod
    def _check_api() -> dict[str, object]:
        from huey.os.api.routers.system import healthz

        payload = healthz()
        return {
            "ready": payload.get("status") == "ok",
            "payload": payload,
        }

    @staticmethod
    def _check_command_center() -> dict[str, object]:
        from huey.apps.command_center.server import create_app

        app = create_app()
        paths = {route.path for route in app.routes}
        return {
            "ready": "/command-center/meta" in paths,
            "route_count": len(paths),
        }

    @staticmethod
    def _check_pyhuey() -> dict[str, object]:
        from huey.connectors.pyhuey.adapter import get_status

        return get_status()

    def _run_healthcheck(self, record: ServiceRecord) -> dict[str, object]:
        if record.healthcheck is None:
            payload = {"ready": record.status == "ready"}
        else:
            try:
                raw = record.healthcheck()
            except (ImportError, OSError, RuntimeError, ValueError) as exc:
                raw = {"ready": False, "error": str(exc)}
            payload = self._normalise_health_payload(raw)

        record.status = "ready" if payload.get("ready") else "blocked"
        record.metadata.update(payload)
        return payload

    @staticmethod
    def _normalise_health_payload(raw: HealthPayload) -> dict[str, object]:
        if raw is None:
            return {"ready": False}
        if isinstance(raw, bool):
            return {"ready": raw}
        if isinstance(raw, str):
            return {"ready": bool(raw), "status": raw}
        payload = dict(raw)
        if "ready" not in payload:
            payload["ready"] = payload.get("status") == "ok"
        return payload


__all__ = ["RuntimeOrchestrator"]
