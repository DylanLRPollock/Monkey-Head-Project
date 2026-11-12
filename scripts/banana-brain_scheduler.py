#!/usr/bin/env python3
"""
banana-brain_scheduler.py — Banana Brain GPU scheduler main executable.

Banana Brain coordinates access to a single primary GPU (NVIDIA Tesla V100
32GB) so that Ollama, ComfyUI, audio workloads and future clients do not
silently exhaust VRAM or interrupt each other. This file is the composition
root: it wires P0 components together, blocks until a shutdown signal, and
tears everything down in dependency order.

The hyphen in the filename means this file cannot be imported as a Python
module. All scheduler logic lives under src/huey/banana_brain/.


Component contract
------------------
Every component must provide:

    async def start(self) -> None    # best-effort; must self-bound its own I/O
    async def stop(self)  -> None    # idempotent; safe to call twice

The scheduler additionally provides:

    def  begin_shutdown(self) -> None     # stop admitting new jobs
    async def wait_for_idle(self) -> None # resolves when in-flight jobs finish

If a component omits the scheduler-specific methods, shutdown degrades
gracefully: begin_shutdown is skipped, wait_for_idle is treated as instant.


Startup order (later depends on earlier):
    job_store -> gpu_monitor -> vram_manager -> priority_manager
    -> ollama_adapter -> comfyui_adapter -> scheduler -> watchdog
    -> scheduler_api

Shutdown order (reverse, with scheduler drained before adapters stop):
    scheduler_api -> watchdog -> scheduler (drain) -> comfyui_adapter
    -> ollama_adapter -> priority_manager -> vram_manager
    -> gpu_monitor -> job_store


Deployment
----------
Designed for Linux/systemd. See deploy/banana-brain.service. Signals:

    SIGINT  / SIGTERM  -> graceful shutdown (first) or forced exit (second)
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Any, Protocol

__version__ = "0.1.0"

LOG = logging.getLogger("banana_brain.main")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXIT_OK = 0
EXIT_STARTUP_FAILURE = 1
EXIT_RUNTIME_FAILURE = 2
EXIT_FORCED = 130

DEFAULT_CONFIG_PATH = Path("config/banana-brain.yaml")
DEFAULT_SHUTDOWN_GRACE = 30.0
COMPONENT_STOP_GRACE = 5.0  # extra seconds per component beyond the main grace

STARTUP_ORDER = (
    "job_store",
    "gpu_monitor",
    "vram_manager",
    "priority_manager",
    "ollama_adapter",
    "comfyui_adapter",
    "scheduler",
    "watchdog",
    "scheduler_api",
)

SHUTDOWN_ORDER = (
    "scheduler_api",
    "watchdog",
    "scheduler",
    "comfyui_adapter",
    "ollama_adapter",
    "priority_manager",
    "vram_manager",
    "gpu_monitor",
    "job_store",
)


class StartupError(RuntimeError):
    """Raised when Banana Brain cannot start safely (config, wiring, or import)."""


class Component(Protocol):
    async def start(self) -> None: ...
    async def stop(self) -> None: ...


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="banana-brain_scheduler.py",
        description="Banana Brain — GPU resource scheduler for HueyOS.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to banana-brain.yaml (default: %(default)s)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        type=str.upper,
        choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
        help="Root log level (default: %(default)s)",
    )
    parser.add_argument(
        "--shutdown-grace",
        type=float,
        default=None,
        metavar="SECONDS",
        help=(
            "Max seconds to wait for in-flight GPU jobs on shutdown "
            f"(default: from config, else {DEFAULT_SHUTDOWN_GRACE:g})"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load config and construct components, then exit without starting",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"banana-brain (huey) {__version__}",
    )
    return parser.parse_args(argv)


def _configure_logging(level: str) -> None:
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level)
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)-8s %(name)s [pid %(process)d]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root.addHandler(handler)
    root.setLevel(level)


def _ensure_package_on_path() -> None:
    """Make the banana_brain package importable when running from a checkout."""
    try:
        import huey.banana_brain  # noqa: F401

        return
    except ImportError:
        pass
    src = Path(__file__).resolve().parent.parent / "src"
    if src.is_dir():
        LOG.debug("adding %s to sys.path", src)
        sys.path.insert(0, str(src))


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def _load_config(path: Path) -> Any:
    from huey.banana_brain.config import load_config

    if not path.exists():
        raise StartupError(f"config file not found: {path}")
    try:
        return load_config(path)
    except Exception as exc:
        raise StartupError(f"failed to load config {path}: {exc}") from exc


def _resolve_grace(cli_value: float | None, config: Any) -> float:
    if cli_value is not None:
        return float(cli_value)
    for attr in ("shutdown_grace_seconds", "shutdown_grace", "grace_seconds"):
        value = getattr(config, attr, None)
        if isinstance(value, (int, float)):
            return float(value)
    return DEFAULT_SHUTDOWN_GRACE


def _describe_device(config: Any) -> str:
    for attr in ("device", "gpu_device", "primary_device"):
        value = getattr(config, attr, None)
        if value is not None:
            return str(value)
    return "default"


# ---------------------------------------------------------------------------
# Component construction (composition root)
# ---------------------------------------------------------------------------


def _construct_components(config: Any) -> dict[str, Any]:
    """
    Instantiate all P0 components without starting them.

    This is the single place where constructor signatures are pinned. If a
    component needs a new dependency, thread it through here rather than
    reaching into globals elsewhere.
    """
    from huey.banana_brain.comfyui_adapter import ComfyUIAdapter
    from huey.banana_brain.gpu_monitor import GPUMonitor
    from huey.banana_brain.job_store import JobStore
    from huey.banana_brain.ollama_adapter import OllamaAdapter
    from huey.banana_brain.priority_manager import PriorityManager
    from huey.banana_brain.scheduler import Scheduler
    from huey.banana_brain.scheduler_api import SchedulerAPI
    from huey.banana_brain.vram_manager import VRAMManager
    from huey.banana_brain.watchdog import Watchdog

    job_store = JobStore(config)
    gpu_monitor = GPUMonitor(config)
    vram_manager = VRAMManager(config, gpu_monitor)
    priority_manager = PriorityManager(config)
    ollama_adapter = OllamaAdapter(config, vram_manager)
    comfyui_adapter = ComfyUIAdapter(config, vram_manager)

    scheduler = Scheduler(
        config=config,
        job_store=job_store,
        gpu_monitor=gpu_monitor,
        vram_manager=vram_manager,
        priority_manager=priority_manager,
        adapters={"ollama": ollama_adapter, "comfyui": comfyui_adapter},
    )
    watchdog = Watchdog(config, scheduler=scheduler, gpu_monitor=gpu_monitor)
    scheduler_api = SchedulerAPI(config, scheduler=scheduler)

    return {
        "job_store": job_store,
        "gpu_monitor": gpu_monitor,
        "vram_manager": vram_manager,
        "priority_manager": priority_manager,
        "ollama_adapter": ollama_adapter,
        "comfyui_adapter": comfyui_adapter,
        "scheduler": scheduler,
        "watchdog": watchdog,
        "scheduler_api": scheduler_api,
    }


# ---------------------------------------------------------------------------
# Shutdown signalling
# ---------------------------------------------------------------------------


class ShutdownController:
    """
    Turns SIGINT/SIGTERM into an awaitable event.

    First signal  -> sets the event; Application begins graceful shutdown.
    Second signal -> forces an immediate exit (os._exit), because the operator
                     explicitly asked for it and we assume components are stuck.
    """

    def __init__(self) -> None:
        self._event: asyncio.Event | None = None
        self._signal_count = 0

    def install(self) -> None:
        loop = asyncio.get_running_loop()
        self._event = asyncio.Event()
        installed: list[signal.Signals] = []
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, self._on_signal, sig)
                installed.append(sig)
            except NotImplementedError:
                LOG.warning("signal %s not supported on this platform", sig.name)
        if not installed:
            raise StartupError("could not install any shutdown signal handlers")
        LOG.debug("installed signal handlers: %s", ", ".join(s.name for s in installed))

    def _on_signal(self, sig: signal.Signals) -> None:
        self._signal_count += 1
        if self._signal_count == 1:
            LOG.warning(
                "received %s; beginning graceful shutdown "
                "(send again to force immediate exit)",
                sig.name,
            )
            if self._event is not None:
                self._event.set()
            return
        LOG.error("received %s again; forcing immediate exit", sig.name)
        logging.shutdown()
        os._exit(EXIT_FORCED)

    async def wait(self) -> None:
        if self._event is None:
            raise RuntimeError("ShutdownController.install() must be called first")
        await self._event.wait()


# ---------------------------------------------------------------------------
# Application lifecycle
# ---------------------------------------------------------------------------


class Application:
    """Owns startup, the block-until-shutdown loop, and ordered teardown."""

    def __init__(
        self,
        config: Any,
        components: dict[str, Any],
        shutdown_grace: float,
    ) -> None:
        self._config = config
        self._components = components
        self._grace = shutdown_grace
        self._started: list[str] = []

    # ---- public ----------------------------------------------------------

    async def run(self, controller: ShutdownController) -> None:
        self._log_banner()
        try:
            await self._start_all()
            LOG.info("banana-brain is ready (pid=%d)", os.getpid())
            await controller.wait()
            LOG.info("shutdown requested")
        finally:
            await self._shutdown_all()

    # ---- startup ---------------------------------------------------------

    def _log_banner(self) -> None:
        LOG.info("banana-brain %s starting", __version__)
        LOG.info("  device:         %s", _describe_device(self._config))
        LOG.info("  shutdown grace: %.1fs", self._grace)
        LOG.info("  components:     %d", len(self._components))

    async def _start_all(self) -> None:
        for name in STARTUP_ORDER:
            component = self._components[name]
            LOG.info("starting %s", name)
            try:
                await component.start()
            except Exception as exc:
                LOG.exception("component %s failed to start", name)
                raise StartupError(f"component {name} failed to start: {exc}") from exc
            self._started.append(name)

    # ---- shutdown --------------------------------------------------------

    async def _shutdown_all(self) -> None:
        if not self._started:
            LOG.info("nothing to shut down")
            return

        LOG.info(
            "shutting down %d component(s), grace %.1fs",
            len(self._started),
            self._grace,
        )

        for name in SHUTDOWN_ORDER:
            if name not in self._started:
                continue
            component = self._components[name]
            if name == "scheduler":
                await self._drain_scheduler(component)
            await self._stop_component(name, component)
            self._started.remove(name)

        LOG.info("shutdown complete")

    async def _drain_scheduler(self, scheduler: Any) -> None:
        """Ask the scheduler to stop admitting jobs, then wait for in-flight ones."""
        begin = getattr(scheduler, "begin_shutdown", None)
        if callable(begin):
            try:
                begin()
            except Exception:
                LOG.exception("scheduler.begin_shutdown failed; continuing to drain")

        wait = getattr(scheduler, "wait_for_idle", None)
        if not callable(wait):
            LOG.debug("scheduler has no wait_for_idle(); skipping drain")
            return

        try:
            await asyncio.wait_for(wait(), timeout=self._grace)
            LOG.info("scheduler drained cleanly")
        except TimeoutError:
            LOG.warning(
                "scheduler did not drain within %.1fs; "
                "pending jobs will be persisted for recovery on next start",
                self._grace,
            )
        except Exception:
            LOG.exception("scheduler drain raised; continuing with shutdown")

    async def _stop_component(self, name: str, component: Any) -> None:
        timeout = self._grace + COMPONENT_STOP_GRACE
        try:
            await asyncio.wait_for(component.stop(), timeout=timeout)
        except TimeoutError:
            LOG.warning("component %s did not stop within %.1fs", name, timeout)
        except Exception:
            LOG.exception("component %s raised during stop", name)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


async def _async_main(args: argparse.Namespace) -> int:
    config = _load_config(args.config)
    components = _construct_components(config)
    LOG.info("constructed %d components", len(components))

    if args.dry_run:
        LOG.info("dry-run: config and wiring validated; not starting components")
        return EXIT_OK

    grace = _resolve_grace(args.shutdown_grace, config)
    app = Application(config, components, shutdown_grace=grace)

    controller = ShutdownController()
    controller.install()
    await app.run(controller)
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    _configure_logging(args.log_level)
    _ensure_package_on_path()

    try:
        return asyncio.run(_async_main(args))
    except StartupError as exc:
        LOG.critical("startup failed: %s", exc)
        return EXIT_STARTUP_FAILURE
    except ImportError as exc:
        LOG.critical("missing Banana Brain component: %s", exc)
        LOG.critical(
            "ensure the banana_brain package is installed or run from a checkout"
        )
        return EXIT_STARTUP_FAILURE
    except KeyboardInterrupt:
        LOG.warning("interrupted before shutdown controller was installed")
        return EXIT_FORCED
    except Exception:
        LOG.exception("unhandled fatal error")
        return EXIT_RUNTIME_FAILURE
    finally:
        logging.shutdown()


if __name__ == "__main__":
    sys.exit(main())
