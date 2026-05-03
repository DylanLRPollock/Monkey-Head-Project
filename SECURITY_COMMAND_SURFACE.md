# SECURITY_COMMAND_SURFACE

This document inventories command/task execution surfaces reviewed in this audit.

| File / Function | Source of input | Reachable remotely | Existing auth / gating | Risk | Recommended fix |
|---|---|---:|---|---|---|
| `src/huey/core/task_scheduler.py` / `TaskScheduler.submit_task` | `command: str` provided by API request or dashboard operator | Indirectly (via API), local GUI direct | Scheduler itself does not execute shell; queues metadata and dispatch state only | **Medium** (free-form command intent preserved for downstream agents) | Keep scheduler execution-free; require strict access controls at submission layers and validate command schema when execution backend is added. |
| `src/huey/memory/PY/api.py` / `submit_task` (`POST /tasks`) | JSON body field `command` | Yes | Existing bearer token middleware when `HUEY_API_TOKEN` configured; **added** local-only guard when token unset | **High** before guard, **Medium** after guard | Keep bearer token mandatory for remote usage; consider command allow-lists per agent capability. |
| `src/huey/memory/PY/api.py` / `dashboard` (`GET /dashboard`) | HTTP request (operator session) and displayed task commands | Yes | Existing bearer token middleware when token set; **added** local-only guard when token unset | **Medium** | Keep as operator surface only; avoid rendering sensitive command payloads to unauthenticated users. |
| `src/huey/memory/PY/dashboard.py` / `DashboardWindow._submit_task_dialog` | Free-form GUI text input | Local desktop operator only | Local interactive GUI, no network exposure by itself | **Medium** | Add explicit developer/operator warning in UI copy when tasks may trigger command execution in downstream agents. |
| `src/huey/memory/PY/commands.py` / `run_command` | Call-site argv sequence | Depends on caller | Uses argv list (`subprocess.run(list(cmd))`), not shell string | **Low** | Preserve argv-only contract; do not accept unparsed free-form shell strings. |
| `src/huey/pygpt_net/tools/manager/__init__.py` / tool runner | Tool registry values forming argv list | Potentially local/automation | Uses list-based `subprocess.run(cmd, check=False)` | **Medium** | Enforce trusted tool registry entries and log provenance of selected command. |

## Explicit checks performed

- Reviewed scheduler submission and API task/dashboard paths.
- Searched for `shell=True`; no hits in `src/huey` / `src/hueyos`.
- Searched for `eval(` / `exec(`; no dynamic code execution hits related to command surfaces.
- Confirmed subprocess usage in maintained paths is argv/list-based.

## Notes

- No obvious `shell=True` usage was found in maintained Python sources under `src/huey` and `src/hueyos`, so no shell-to-argv conversion patch was required in this audit.
- Developer-only task entry points are preserved; this change narrows unauthenticated remote exposure by enforcing local-only behavior when no API token is configured.
