# Tool and Plugin Permission Boundaries (PyHuey/MonkeyManager)

This note documents execution boundaries for `huey.pygpt_net.tools.manager.MonkeyManager`.

## Execution surfaces

- **Filesystem + shell**: `_run_script()` invokes local installer/runtime scripts via `subprocess.run()`.
- **Container/Kubernetes operations**: menu actions call `huey.services.container_management` helpers.
- **System checks**: `run_system_check()` executes HueyOS local environment checks.
- **Provider/network/browser/python execution**: not directly executed by this manager module.

## Failure handling

- Missing scripts are logged at error level.
- Non-zero script exit codes are logged at error level.
- Script launch errors (`OSError`) are logged with traceback.
- Optional UI imports now catch only `ImportError`/`ModuleNotFoundError`.

## Destructive operation intent gate

The following actions are treated as destructive and require explicit operator intent:

- `monkey.docker.stop`
- `monkey.docker.clean`
- `monkey.k8s.cleanup`

Intent gate:

- Set environment variable `HUEY_TOOL_ALLOW_DESTRUCTIVE=1` before invoking the action.
- If unset, the action is blocked and a warning is logged.

This is an incremental hardening step and does not redesign the plugin system.
