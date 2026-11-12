#!/usr/bin/env python3
"""
banana_brain.scheduler_cli — command-line client for the Banana Brain API.

Talks to scheduler_api.py over a Unix socket (default) or TCP (bearer token
required). Every command maps to a single API call; output is human-readable
by default and JSON with --json.

Run as:
    python -m huey.banana_brain.scheduler_cli <command> [args]
    banana-brain <command> [args]         (when installed via entry point)

Common options:

  --config PATH     config file used to discover the API
                    (default: config/banana-brain.yaml)
  --socket PATH     explicit Unix socket (overrides config)
  --url URL         explicit TCP base URL (overrides config)
  --token TOKEN     bearer token for TCP (or env BANANA_BRAIN_TOKEN)
  --json            emit machine-readable JSON

Commands (abridged; see --help for each):

  health                                     liveness probe
  status                                     overall snapshot
  jobs list [--state S] [--limit N]
  jobs show ID
  jobs submit FILE                           FILE may be '-' for stdin
  jobs cancel ID [--force]
  jobs watch ID [--interval S] [--timeout S]
  jobs events ID [--limit N]
  jobs priority ID NEW_PRIORITY              cancel + resubmit (see note)
  queue [--limit N]
  suspended list
  suspended cancel ID
  mode get
  mode set {ai,image,mixed,maintenance,gaming} [--reason R] [--force]
  mode resume [--reason R]
  mode clear-halt --reason R [--cleared-by C]
  pause [--reason R]                         alias for 'mode set maintenance'
  resume [--reason R]                        alias for 'mode resume'
  vram
  watchdog [snapshot]
  watchdog ack KEY
  adapters

Exit codes:

  0   success
  1   application error (API returned 4xx/5xx, job not found, etc.)
  2   usage error (argparse)
  3   transport error (cannot reach API)

Notes:

  'jobs priority' has no in-place equivalent in the API yet. It performs
  cancel + resubmit and produces a new job id; it refuses running jobs.
  See the function docstring for the exact semantics.

  'pause' is a mode transition to 'maintenance'. Any jobs suspended by the
  transition remain queued; 'resume' restores the mode that was active
  before 'pause' (or the default if none).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

import aiohttp

__all__ = ["ExitCode", "main"]


LOG = logging.getLogger("banana_brain.cli")

#: Terminal job states (kept local so the CLI does not need job_models on
#: the import path when invoked as a standalone script from a checkout).
_TERMINAL_STATES = frozenset({"completed", "failed", "cancelled"})
_VALID_MODES = ("ai", "image", "mixed", "maintenance", "gaming")

#: Priorities accepted by 'jobs priority' beyond plain integers.
_PRIORITY_NAMES = {
    "SAFETY": 100,
    "EXCLUSIVE": 90,
    "INTERACTIVE": 80,
    "IMAGE": 70,
    "AUDIO": 60,
    "BACKGROUND": 40,
    "BATCH": 20,
    "MAINTENANCE": 10,
}


# ---------------------------------------------------------------------------
# Exit codes
# ---------------------------------------------------------------------------


class ExitCode:
    OK = 0
    APP_ERROR = 1
    USAGE = 2
    TRANSPORT = 3


# ---------------------------------------------------------------------------
# API client
# ---------------------------------------------------------------------------


class APIError(Exception):
    """Application-level error returned by the API or produced by the CLI."""

    def __init__(self, status: int, message: str) -> None:
        self.status = status
        self.message = message
        super().__init__(status, message)

    def __str__(self) -> str:
        return f"HTTP {self.status}: {self.message}"


class Client:
    """Async HTTP client over a Unix socket or TCP."""

    def __init__(
        self,
        *,
        socket_path: str | None = None,
        base_url: str | None = None,
        token: str | None = None,
        timeout_s: float = 30.0,
    ) -> None:
        if not socket_path and not base_url:
            raise ValueError("one of socket_path or base_url is required")
        self._socket_path = socket_path
        self._base_url = base_url
        self._token = token
        self._timeout_s = timeout_s
        self._session: aiohttp.ClientSession | None = None

    @property
    def endpoint(self) -> str:
        if self._base_url:
            return self._base_url
        return f"unix:{self._socket_path}"

    async def __aenter__(self) -> Client:
        headers = {"Accept": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        timeout = aiohttp.ClientTimeout(total=self._timeout_s)
        if self._base_url:
            self._session = aiohttp.ClientSession(
                headers=headers, timeout=timeout, trust_env=False
            )
        else:
            assert self._socket_path is not None
            connector = aiohttp.UnixConnector(path=self._socket_path)
            self._session = aiohttp.ClientSession(
                connector=connector,
                headers=headers,
                timeout=timeout,
                trust_env=False,
            )
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def request(
        self,
        method: str,
        path: str,
        json_body: dict[str, Any] | None = None,
    ) -> tuple[int, Any]:
        if self._session is None:
            raise RuntimeError("Client used outside of async with")
        base = self._base_url or "http://localhost"
        url = f"{base}{path}"
        try:
            async with self._session.request(method, url, json=json_body) as resp:
                text = await resp.text()
                if not text:
                    return resp.status, None
                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    data = {"raw": text}
                return resp.status, data
        except aiohttp.ClientConnectorError:
            raise
        except aiohttp.ClientError as exc:
            raise APIError(0, f"transport error: {exc}") from exc

    async def request_ok(
        self,
        method: str,
        path: str,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        status, data = await self.request(method, path, json_body)
        if 200 <= status < 300:
            return data
        message = _extract_error_message(data)
        raise APIError(status, message)


def _extract_error_message(data: Any) -> str:
    if isinstance(data, dict):
        err = data.get("error")
        if isinstance(err, dict):
            msg = err.get("message")
            if isinstance(msg, str):
                return msg
        if isinstance(err, str):
            return err
    if isinstance(data, dict) and "raw" in data:
        return str(data["raw"])[:400]
    return f"HTTP error; response body: {data!r}" if data else "unknown error"


# ---------------------------------------------------------------------------
# Endpoint resolution
# ---------------------------------------------------------------------------


def _resolve_config_path(raw: str | None) -> Path | None:
    if not raw:
        return None
    p = Path(raw).expanduser()
    return p if p.exists() else None


def _load_config_safe(path: Path | None) -> Any:
    if path is None:
        return None
    try:
        from huey.banana_brain.config import ConfigError, load_config
    except ImportError:
        LOG.debug("huey.banana_brain.config not importable; skipping")
        return None
    try:
        return load_config(path)
    except ConfigError as exc:
        LOG.warning("could not load config %s: %s", path, exc)
        return None


def _build_client(args: argparse.Namespace) -> Client:
    config = _load_config_safe(_resolve_config_path(args.config))

    # Transport: explicit --url wins, then --socket, then config.
    if args.url:
        base_url = args.url
        socket_path = None
    elif args.socket:
        base_url = None
        socket_path = args.socket
    elif config is not None and getattr(config, "api_bind", None):
        base_url = f"http://{config.api_bind}"
        socket_path = None
    else:
        base_url = None
        socket_path = (
            str(getattr(config, "api_socket_path", None))
            if config is not None and getattr(config, "api_socket_path", None)
            else "data/banana-brain.sock"
        )

    # Token: explicit --token, then env, then config (only used for TCP).
    token = args.token or os.environ.get("BANANA_BRAIN_TOKEN")
    if not token and config is not None:
        token = getattr(config, "api_token", None)

    if not base_url and not token:
        # Unix socket auth is filesystem-based; a token is ignored, but we
        # still allow passing one so a shared script can target both.
        pass

    return Client(
        socket_path=socket_path,
        base_url=base_url,
        token=token if token else None,
    )


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _fmt_duration(seconds: float | None) -> str:
    if seconds is None:
        return "-"
    try:
        s = max(0, round(float(seconds)))
    except (TypeError, ValueError):
        return "-"
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m{s % 60:02d}s"
    if s < 86400:
        return f"{s // 3600}h{(s % 3600) // 60:02d}m"
    return f"{s // 86400}d{(s % 86400) // 3600:02d}h"


def _fmt_bytes(n: int | None) -> str:
    if n is None:
        return "-"
    try:
        b = float(n)
    except (TypeError, ValueError):
        return "-"
    if b < 1024:
        return f"{int(b)} B"
    for unit in ("KiB", "MiB", "GiB", "TiB"):
        b /= 1024
        if b < 1024 or unit == "TiB":
            return f"{b:.1f} {unit}"
    return f"{b:.1f} TiB"


def _fmt_ts(ts: float | None) -> str:
    if ts is None:
        return "-"
    try:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(float(ts)))
    except (TypeError, ValueError, OverflowError):
        return "-"


def _short_id(job_id: Any, width: int = 8) -> str:
    if not job_id:
        return "-"
    text = str(job_id)
    return text[:width] if len(text) > width else text


def _print_json(data: Any, stream: Any = None) -> None:
    print(json.dumps(data, indent=2, default=str), file=stream or sys.stdout)


def _print_table(rows: list[list[str]], headers: list[str], stream: Any = None) -> None:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers), file=stream or sys.stdout)
    print("  ".join("-" * w for w in widths), file=stream or sys.stdout)
    for row in rows:
        print(fmt.format(*row), file=stream or sys.stdout)


# ---------------------------------------------------------------------------
# Commands — health/status
# ---------------------------------------------------------------------------


async def _cmd_health(args: argparse.Namespace, client: Client) -> int:
    status, data = await client.request("GET", "/health")
    if args.json:
        _print_json(data)
    else:
        print(f"status:            {status}")
        if isinstance(data, dict):
            print(f"ok:                {data.get('ok')}")
            print(f"shutting_down:     {data.get('shutting_down')}")
            print(f"mode:              {data.get('mode')}")
            print(f"watchdog_severity: {data.get('watchdog_severity')}")
            print(f"api_version:       {data.get('api_version')}")
    return ExitCode.OK if 200 <= status < 300 else ExitCode.APP_ERROR


async def _cmd_status(args: argparse.Namespace, client: Client) -> int:
    data = await client.request_ok("GET", "/status")
    if args.json:
        _print_json(data)
        return ExitCode.OK

    sched = data.get("scheduler") or {}
    mode = data.get("mode") or {}
    wd = data.get("watchdog") or {}
    gpu = data.get("gpu") or {}

    print(f"uptime:        {_fmt_duration(data.get('uptime_seconds'))}")
    print(f"mode:          {mode.get('mode') or '-'}", end="")
    if mode.get("safety_halted"):
        print(f"  (SAFETY HALTED: {mode.get('safety_halt_reason')})")
    else:
        print()
    print(f"shutting_down: {sched.get('shutting_down')}")
    print(f"current_job:   {_short_id(sched.get('current_job_id'))}")
    print(f"pending_jobs:  {sched.get('pending_jobs')}")
    print(f"adapters:      {', '.join(data.get('adapters') or []) or '-'}")

    if gpu.get("identity"):
        ident = gpu["identity"]
        print(
            f"gpu:           {ident.get('name')} "
            f"(index={ident.get('index')}, uuid={ident.get('uuid')})"
        )
        print(
            f"vram:          "
            f"{_fmt_bytes(gpu.get('used_vram_bytes'))} used / "
            f"{_fmt_bytes(gpu.get('total_vram_bytes'))} total "
            f"({_fmt_bytes(gpu.get('free_vram_bytes'))} free)"
        )
        print(
            f"temp / power:  {gpu.get('temperature_c')}°C / "
            f"{gpu.get('power_watts')} W"
        )

    signals = wd.get("signals") or []
    if signals:
        print(f"watchdog:      {len(signals)} active signal(s):")
        for sig in signals:
            print(
                f"  - [{sig.get('severity')}] {sig.get('name')}: "
                f"{sig.get('message')}"
            )
    else:
        print("watchdog:      no active signals")

    return ExitCode.OK


# ---------------------------------------------------------------------------
# Commands — jobs
# ---------------------------------------------------------------------------


async def _cmd_jobs_list(args: argparse.Namespace, client: Client) -> int:
    params = f"?limit={args.limit}"
    if args.state:
        params += f"&state={args.state}"
    data = await client.request_ok("GET", f"/jobs{params}")
    jobs = data.get("jobs") or []

    if args.json:
        _print_json(data)
        return ExitCode.OK

    if not jobs:
        print("no jobs")
        return ExitCode.OK

    rows = [
        [
            _short_id(j.get("id")),
            str(j.get("adapter") or "-"),
            str(j.get("state") or "-"),
            str(j.get("priority", "-")),
            _fmt_duration(
                (time.time() - j["submitted_at"]) if j.get("submitted_at") else None
            ),
            _fmt_ts(j.get("submitted_at")),
        ]
        for j in jobs
    ]
    _print_table(rows, ["ID", "ADAPTER", "STATE", "PRI", "AGE", "SUBMITTED"])
    return ExitCode.OK


async def _cmd_jobs_show(args: argparse.Namespace, client: Client) -> int:
    job = await client.request_ok("GET", f"/jobs/{args.id}")
    if args.json:
        _print_json(job)
        return ExitCode.OK

    print(f"id:              {job.get('id')}")
    print(f"adapter:         {job.get('adapter')}")
    print(f"state:           {job.get('state')}")
    print(f"priority:        {job.get('priority')}")
    print(f"exclusive:       {job.get('exclusive')}")
    print(f"owner:           {job.get('owner')}")
    print(f"submitted:       {_fmt_ts(job.get('submitted_at'))}")
    print(f"started:         {_fmt_ts(job.get('started_at'))}")
    print(f"finished:        {_fmt_ts(job.get('finished_at'))}")
    print(f"attempts:        " f"{job.get('attempts')}/{job.get('max_attempts')}")
    if job.get("estimated_vram_bytes"):
        print(f"est. vram:       " f"{_fmt_bytes(job['estimated_vram_bytes'])}")
    if job.get("deadline"):
        print(
            f"deadline:        {_fmt_ts(job['deadline'])} "
            f"({_fmt_duration(job['deadline'] - time.time())} remaining)"
        )
    if job.get("idempotency_key"):
        print(f"idempotency:     {job['idempotency_key']}")
    if job.get("last_error"):
        print(f"last error:      {job['last_error']}")
    if job.get("result") is not None:
        print("result:")
        _print_json(job["result"])
    return ExitCode.OK


async def _cmd_jobs_submit(args: argparse.Namespace, client: Client) -> int:
    if args.file == "-":
        raw = sys.stdin.read()
    else:
        path = Path(args.file)
        if not path.exists():
            raise APIError(0, f"file not found: {path}")
        raw = path.read_text(encoding="utf-8")
    try:
        body = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise APIError(0, f"invalid JSON in submission: {exc}") from exc
    if not isinstance(body, dict):
        raise APIError(0, "submission must be a JSON object")
    job = await client.request_ok("POST", "/jobs", body)
    if args.json:
        _print_json(job)
    else:
        print(
            f"submitted job {job.get('id')} "
            f"(adapter={job.get('adapter')}, state={job.get('state')})"
        )
    return ExitCode.OK


async def _cmd_jobs_cancel(args: argparse.Namespace, client: Client) -> int:
    body = {"force": bool(args.force)}
    data = await client.request_ok("POST", f"/jobs/{args.id}/cancel", body)
    if args.json:
        _print_json(data)
    else:
        print(
            f"cancelled job {args.id} (state={data.get('state')}, "
            f"force={data.get('force')})"
        )
    return ExitCode.OK


async def _cmd_jobs_watch(args: argparse.Namespace, client: Client) -> int:
    deadline = time.time() + args.timeout
    last_state: str | None = None
    while True:
        job = await client.request_ok("GET", f"/jobs/{args.id}")
        state = str(job.get("state") or "")
        if state != last_state:
            print(
                f"[{_fmt_ts(time.time())}] state={state}",
                file=sys.stderr,
            )
            last_state = state
        if state in _TERMINAL_STATES:
            if args.json:
                _print_json(job)
            else:
                print(f"final state: {state}")
                if job.get("last_error"):
                    print(f"error: {job['last_error']}")
            return ExitCode.OK
        if time.time() >= deadline:
            raise APIError(
                504,
                f"job {args.id} did not finish within {args.timeout}s",
            )
        await asyncio.sleep(args.interval)


async def _cmd_jobs_events(args: argparse.Namespace, client: Client) -> int:
    data = await client.request_ok("GET", f"/jobs/{args.id}/events?limit={args.limit}")
    events = data.get("events") or []
    if args.json:
        _print_json(data)
        return ExitCode.OK
    if not events:
        print("no events")
        return ExitCode.OK
    rows = [
        [
            _fmt_ts(e.get("at")),
            str(e.get("kind") or "-"),
            (
                f"{e.get('from_state') or '-'} -> {e.get('to_state') or '-'}"
                if e.get("kind") == "transition"
                else "-"
            ),
            json.dumps(e.get("detail")) if e.get("detail") else "-",
        ]
        for e in events
    ]
    _print_table(rows, ["TIME", "KIND", "TRANSITION", "DETAIL"])
    return ExitCode.OK


async def _cmd_jobs_priority(args: argparse.Namespace, client: Client) -> int:
    """
    Change a job's priority.

    The API has no in-place priority update. The CLI implements this as
    cancel + resubmit:

      1. Fetch the current job.
      2. Refuse if state is 'running' or terminal.
      3. POST /jobs/{id}/cancel.
      4. POST /jobs with the same fields, updated priority, and no
         idempotency_key (to prevent dedup against the cancelled job).

    The replacement job has a new id. If the original is still present in
    job_store, both will be visible in 'jobs list' until the store prunes
    the cancelled one.
    """
    job = await client.request_ok("GET", f"/jobs/{args.id}")
    state = str(job.get("state") or "")
    if state in _TERMINAL_STATES:
        raise APIError(409, f"job {args.id} is already {state}; nothing to do")
    if state == "running":
        raise APIError(
            409,
            f"job {args.id} is running; cancel it first "
            f"(banana-brain jobs cancel {args.id}) or use 'mode' to stop "
            f"the queue",
        )

    new_priority = _parse_priority_arg(args.priority)

    await client.request_ok("POST", f"/jobs/{args.id}/cancel", {"force": False})

    body: dict[str, Any] = {
        "adapter": job.get("adapter"),
        "payload": job.get("payload") or {},
        "priority": new_priority,
        "exclusive": bool(job.get("exclusive", False)),
        "deadline": job.get("deadline"),
        "estimated_vram_bytes": job.get("estimated_vram_bytes"),
        "owner": job.get("owner"),
        "tags": job.get("tags") or {},
        "max_attempts": job.get("max_attempts", 1),
    }
    new_job = await client.request_ok("POST", "/jobs", body)

    result = {
        "old_job_id": args.id,
        "new_job_id": new_job.get("id"),
        "priority": new_priority,
    }
    if args.json:
        _print_json(result)
    else:
        print(
            f"replaced {args.id} with {new_job.get('id')} "
            f"at priority {new_priority}"
        )
        print(
            "note: this is a cancel + resubmit; the new job has a fresh id "
            "and its attempts counter starts at 0",
            file=sys.stderr,
        )
    return ExitCode.OK


def _parse_priority_arg(raw: str) -> int:
    raw_stripped = raw.strip()
    if raw_stripped.upper() in _PRIORITY_NAMES:
        return _PRIORITY_NAMES[raw_stripped.upper()]
    try:
        value = int(raw_stripped)
    except ValueError:
        raise APIError(
            2,
            f"invalid priority {raw!r}; use an integer or one of "
            f"{', '.join(_PRIORITY_NAMES)}",
        ) from None
    if not (0 <= value <= 100):
        raise APIError(2, f"priority must be in [0, 100], got {value}")
    return value


# ---------------------------------------------------------------------------
# Commands — queue, suspended
# ---------------------------------------------------------------------------


async def _cmd_queue(args: argparse.Namespace, client: Client) -> int:
    path = "/queue"
    if args.limit is not None:
        path += f"?limit={args.limit}"
    data = await client.request_ok("GET", path)
    entries = data.get("entries") or []

    if args.json:
        _print_json(data)
        return ExitCode.OK

    print(f"queue size: {data.get('size')}")
    if not entries:
        return ExitCode.OK
    rows = [
        [
            _short_id(e.get("id")),
            str(e.get("adapter") or "-"),
            str(e.get("state") or "-"),
            str(e.get("base_priority")),
            str(e.get("effective_priority")),
            str(e.get("aging_bonus")),
            "yes" if e.get("overdue") else "-",
            _fmt_duration(e.get("age_seconds")),
        ]
        for e in entries
    ]
    _print_table(
        rows,
        ["ID", "ADAPTER", "STATE", "BASE", "EFF", "AGED", "OVERDUE", "AGE"],
    )
    return ExitCode.OK


async def _cmd_suspended_list(args: argparse.Namespace, client: Client) -> int:
    data = await client.request_ok("GET", "/suspended")
    jobs = data.get("jobs") or []
    if args.json:
        _print_json(data)
        return ExitCode.OK
    if not jobs:
        print("no suspended jobs")
        return ExitCode.OK
    rows = [
        [
            _short_id(j.get("id")),
            str(j.get("adapter") or "-"),
            str(j.get("priority")),
            _fmt_duration(j.get("age_seconds")),
        ]
        for j in jobs
    ]
    _print_table(rows, ["ID", "ADAPTER", "PRI", "AGE"])
    return ExitCode.OK


async def _cmd_suspended_cancel(args: argparse.Namespace, client: Client) -> int:
    data = await client.request_ok("POST", f"/suspended/{args.id}/cancel", {})
    if args.json:
        _print_json(data)
    else:
        print(f"cancelled suspended job {args.id}")
    return ExitCode.OK


# ---------------------------------------------------------------------------
# Commands — mode
# ---------------------------------------------------------------------------


async def _cmd_mode_get(args: argparse.Namespace, client: Client) -> int:
    data = await client.request_ok("GET", "/mode")
    if args.json:
        _print_json(data)
        return ExitCode.OK
    print(f"mode:              {data.get('mode')}")
    print(
        f"since:             {_fmt_ts(data.get('mode_since'))} "
        f"({_fmt_duration(data.get('mode_age_seconds'))} ago)"
    )
    print(f"reason:            {data.get('mode_reason')}")
    print(f"requested_by:      {data.get('mode_requested_by')}")
    print(f"safety_halted:     {data.get('safety_halted')}")
    if data.get("safety_halt_reason"):
        print(f"halt_reason:       {data.get('safety_halt_reason')}")
    print(f"previous_mode:     {data.get('previous_non_exclusive_mode')}")
    print(f"suspended_jobs:    {data.get('suspended_jobs')}")
    print(f"current_job:       {_short_id(data.get('current_job_id'))}")
    return ExitCode.OK


async def _cmd_mode_set(args: argparse.Namespace, client: Client) -> int:
    body = {
        "mode": args.mode,
        "reason": args.reason,
        "force": bool(args.force),
    }
    data = await client.request_ok("POST", "/mode", body)
    if args.json:
        _print_json(data)
        return ExitCode.OK
    if data.get("success"):
        print(
            f"mode: {data.get('from_mode')} -> {data.get('to_mode')} "
            f"({_fmt_duration(data.get('elapsed_s'))})"
        )
    else:
        print(
            f"mode: {data.get('from_mode')} -> {data.get('to_mode')} "
            f"(incomplete: {data.get('error')})"
        )
    if data.get("suspended_count"):
        print(f"suspended {data['suspended_count']} job(s)")
    if data.get("interrupted_job_id"):
        print(
            f"warning: job {data['interrupted_job_id']} still running",
            file=sys.stderr,
        )
    return ExitCode.OK if data.get("success") else ExitCode.APP_ERROR


async def _cmd_mode_resume(args: argparse.Namespace, client: Client) -> int:
    data = await client.request_ok("POST", "/mode/resume", {"reason": args.reason})
    if args.json:
        _print_json(data)
    else:
        print(
            f"resumed to mode: {data.get('to_mode')} "
            f"({_fmt_duration(data.get('elapsed_s'))})"
        )
    return ExitCode.OK if data.get("success") else ExitCode.APP_ERROR


async def _cmd_mode_clear_halt(args: argparse.Namespace, client: Client) -> int:
    body = {"reason": args.reason, "cleared_by": args.cleared_by}
    data = await client.request_ok("POST", "/mode/clear-halt", body)
    if args.json:
        _print_json(data)
    else:
        print(f"safety halt cleared (safety_halted={data.get('safety_halted')})")
    return ExitCode.OK


async def _cmd_pause(args: argparse.Namespace, client: Client) -> int:
    # Documented alias: pause == transition to maintenance mode.
    data = await client.request_ok(
        "POST",
        "/mode",
        {
            "mode": "maintenance",
            "reason": f"pause: {args.reason}",
            "force": False,
        },
    )
    if args.json:
        _print_json(data)
    else:
        print(f"paused (mode: {data.get('from_mode')} -> {data.get('to_mode')})")
        print(
            "note: 'pause' is a mode transition; use 'resume' to return to "
            "the previous non-exclusive mode",
            file=sys.stderr,
        )
    return ExitCode.OK if data.get("success") else ExitCode.APP_ERROR


async def _cmd_resume(args: argparse.Namespace, client: Client) -> int:
    data = await client.request_ok(
        "POST", "/mode/resume", {"reason": f"resume: {args.reason}"}
    )
    if args.json:
        _print_json(data)
    else:
        print(f"resumed to mode: {data.get('to_mode')}")
    return ExitCode.OK if data.get("success") else ExitCode.APP_ERROR


# ---------------------------------------------------------------------------
# Commands — vram, watchdog, adapters
# ---------------------------------------------------------------------------


async def _cmd_vram(args: argparse.Namespace, client: Client) -> int:
    data = await client.request_ok("GET", "/vram")
    if args.json:
        _print_json(data)
        return ExitCode.OK

    print(f"gpu_state_known:  {data.get('gpu_state_known')}")
    print(f"total:            {_fmt_bytes(data.get('total_vram_bytes'))}")
    print(f"free:             {_fmt_bytes(data.get('free_vram_bytes'))}")
    print(f"committed:        {_fmt_bytes(data.get('committed_bytes'))}")
    print(f"headroom:         {_fmt_bytes(data.get('headroom_bytes'))}")
    print(f"allocatable:      {_fmt_bytes(data.get('allocatable_bytes'))}")
    print(f"reservations:     {data.get('reservation_count')}")
    for r in data.get("reservations") or []:
        print(
            f"  - {_short_id(r.get('job_id'))} "
            f"({r.get('adapter')}) {_fmt_bytes(r.get('bytes'))} "
            f"[{r.get('state')}] age={_fmt_duration(r.get('age_seconds'))}"
        )
    if data.get("last_refusal"):
        print(f"last_refusal:     {data['last_refusal']}")
    return ExitCode.OK


async def _cmd_watchdog(args: argparse.Namespace, client: Client) -> int:
    sub = args.watchdog_command or "snapshot"
    if sub == "snapshot":
        data = await client.request_ok("GET", "/watchdog")
        if args.json:
            _print_json(data)
            return ExitCode.OK
        print(f"running:           {data.get('running')}")
        print(f"run_count:         {data.get('run_count')}")
        print(
            f"last_run:          {_fmt_ts(data.get('last_run_at'))} "
            f"({_fmt_duration(_now_minus(data.get('last_run_at')))} ago)"
        )
        print(f"check_interval:    {data.get('check_interval_s')}s")
        signals = data.get("signals") or []
        if not signals:
            print("signals:           none")
        else:
            print(f"signals:           {len(signals)}")
            for sig in signals:
                print(
                    f"  - [{sig.get('severity')}] {sig.get('name')}: "
                    f"{sig.get('message')}  (key={sig.get('key')})"
                )
        if data.get("cancel_requested"):
            print(f"cancel_requested:  {data['cancel_requested']}")
        if data.get("service_failures"):
            print(f"service_failures:  {data['service_failures']}")
        return ExitCode.OK
    if sub == "ack":
        data = await client.request_ok("POST", "/watchdog/ack", {"key": args.key})
        if args.json:
            _print_json(data)
        else:
            print(f"acknowledged signal {args.key}")
        return ExitCode.OK
    raise APIError(2, f"unknown watchdog subcommand {sub!r}")


async def _cmd_adapters(args: argparse.Namespace, client: Client) -> int:
    data = await client.request_ok("GET", "/adapters")
    adapters = data.get("adapters") or []
    if args.json:
        _print_json(data)
        return ExitCode.OK
    if not adapters:
        print("no adapters registered")
    for name in adapters:
        print(name)
    return ExitCode.OK


def _now_minus(ts: float | None) -> float | None:
    if ts is None:
        return None
    return time.time() - float(ts)


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


async def _dispatch(args: argparse.Namespace, client: Client) -> int:
    handler = _HANDLERS.get(_route_key(args))
    if handler is None:
        raise APIError(2, f"no handler for {_route_key(args)}")
    return await handler(args, client)


def _route_key(args: argparse.Namespace) -> tuple[str, ...]:
    command = args.command
    if command == "jobs":
        return ("jobs", args.jobs_command)
    if command == "suspended":
        return ("suspended", args.suspended_command)
    if command == "mode":
        return ("mode", args.mode_command or "get")
    if command == "watchdog":
        return ("watchdog", args.watchdog_command or "snapshot")
    return (command,)


_HANDLERS: dict[tuple[str, ...], Any] = {
    ("health",): _cmd_health,
    ("status",): _cmd_status,
    ("adapters",): _cmd_adapters,
    ("jobs", "list"): _cmd_jobs_list,
    ("jobs", "show"): _cmd_jobs_show,
    ("jobs", "submit"): _cmd_jobs_submit,
    ("jobs", "cancel"): _cmd_jobs_cancel,
    ("jobs", "watch"): _cmd_jobs_watch,
    ("jobs", "events"): _cmd_jobs_events,
    ("jobs", "priority"): _cmd_jobs_priority,
    ("queue",): _cmd_queue,
    ("suspended", "list"): _cmd_suspended_list,
    ("suspended", "cancel"): _cmd_suspended_cancel,
    ("mode", "get"): _cmd_mode_get,
    ("mode", "set"): _cmd_mode_set,
    ("mode", "resume"): _cmd_mode_resume,
    ("mode", "clear-halt"): _cmd_mode_clear_halt,
    ("pause",): _cmd_pause,
    ("resume",): _cmd_resume,
    ("vram",): _cmd_vram,
    ("watchdog", "snapshot"): _cmd_watchdog,
    ("watchdog", "ack"): _cmd_watchdog,
}


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="banana-brain",
        description="Command-line client for the Banana Brain GPU scheduler.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config",
        default="config/banana-brain.yaml",
        help="config file used to discover the API " "(default: %(default)s)",
    )
    parser.add_argument(
        "--socket",
        default=None,
        help="explicit Unix socket path (overrides config)",
    )
    parser.add_argument(
        "--url",
        default=None,
        help="explicit TCP base URL (overrides config); requires --token "
        "or BANANA_BRAIN_TOKEN",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="bearer token for TCP (or env BANANA_BRAIN_TOKEN)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON instead of human-readable text",
    )
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help="CLI log level (default: %(default)s)",
    )

    subs = parser.add_subparsers(dest="command", required=True)

    subs.add_parser("health", help="liveness probe")
    subs.add_parser("status", help="overall snapshot")

    # jobs
    jobs = subs.add_parser("jobs", help="job management")
    jobs_subs = jobs.add_subparsers(dest="jobs_command", required=True)

    p = jobs_subs.add_parser("list", help="list recent jobs")
    p.add_argument("--state", default=None, help="comma-separated states to filter on")
    p.add_argument("--limit", type=int, default=50)

    p = jobs_subs.add_parser("show", help="show one job")
    p.add_argument("id")

    p = jobs_subs.add_parser("submit", help="submit a job from JSON file")
    p.add_argument("file", help="path to a JSON job file, or '-' for stdin")

    p = jobs_subs.add_parser("cancel", help="cancel a job")
    p.add_argument("id")
    p.add_argument(
        "--force", action="store_true", help="request cancellation of a running job"
    )

    p = jobs_subs.add_parser("watch", help="poll a job until it terminates")
    p.add_argument("id")
    p.add_argument("--interval", type=float, default=1.0)
    p.add_argument("--timeout", type=float, default=3600.0)

    p = jobs_subs.add_parser("events", help="list a job's event log")
    p.add_argument("id")
    p.add_argument("--limit", type=int, default=100)

    p = jobs_subs.add_parser(
        "priority",
        help="change a pending job's priority (cancel + resubmit)",
    )
    p.add_argument("id")
    p.add_argument(
        "priority",
        help="new priority (integer 0-100 or a name such as INTERACTIVE)",
    )

    # queue
    p = subs.add_parser("queue", help="show the priority queue")
    p.add_argument("--limit", type=int, default=None)

    # suspended
    suspended = subs.add_parser("suspended", help="jobs suspended by exclusive modes")
    suspended_subs = suspended.add_subparsers(dest="suspended_command", required=True)
    suspended_subs.add_parser("list", help="list suspended jobs")
    p = suspended_subs.add_parser("cancel", help="cancel a suspended job")
    p.add_argument("id")

    # mode
    mode = subs.add_parser("mode", help="GPU mode management")
    mode_subs = mode.add_subparsers(dest="mode_command", required=False)
    mode_subs.add_parser("get", help="show current mode")
    p = mode_subs.add_parser("set", help="transition to a different mode")
    p.add_argument("mode", choices=_VALID_MODES)
    p.add_argument("--reason", default="cli")
    p.add_argument(
        "--force",
        action="store_true",
        help="request cancellation of the current job before " "waiting",
    )
    p = mode_subs.add_parser("resume", help="leave an exclusive mode")
    p.add_argument("--reason", default="cli resume")
    p = mode_subs.add_parser("clear-halt", help="clear the safety overlay")
    p.add_argument("--reason", required=True)
    p.add_argument("--cleared-by", default="cli")

    # pause / resume (documented aliases)
    p = subs.add_parser(
        "pause",
        help="pause (transition to maintenance mode; use 'resume' to return)",
    )
    p.add_argument("--reason", default="paused via CLI")
    p = subs.add_parser(
        "resume", help="resume from 'pause' (return to the previous mode)"
    )
    p.add_argument("--reason", default="resumed via CLI")

    # vram
    subs.add_parser("vram", help="VRAM manager snapshot")

    # watchdog
    watchdog = subs.add_parser("watchdog", help="watchdog snapshot and ack")
    watchdog_subs = watchdog.add_subparsers(dest="watchdog_command", required=False)
    watchdog_subs.add_parser("snapshot", help="show watchdog state")
    p = watchdog_subs.add_parser("ack", help="acknowledge a signal by key")
    p.add_argument("key")

    # adapters
    subs.add_parser("adapters", help="list registered adapters")

    return parser


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


async def _async_main(args: argparse.Namespace) -> int:
    client = _build_client(args)
    try:
        async with client:
            return await _dispatch(args, client)
    except aiohttp.ClientConnectorError as exc:
        print(
            f"error: cannot reach Banana Brain API at {client.endpoint}",
            file=sys.stderr,
        )
        print(f"       {exc}", file=sys.stderr)
        print(
            "hint: verify --socket/--url and that banana-brain is running",
            file=sys.stderr,
        )
        return ExitCode.TRANSPORT


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    try:
        return asyncio.run(_async_main(args))
    except APIError as exc:
        print(f"error: {exc.message}", file=sys.stderr)
        return ExitCode.APP_ERROR
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return ExitCode.APP_ERROR
    except Exception:
        LOG.exception("unhandled error")
        return ExitCode.APP_ERROR


if __name__ == "__main__":
    sys.exit(main())
