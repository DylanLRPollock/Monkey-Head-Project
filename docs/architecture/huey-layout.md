# HueyOS Repository Layout

HueyOS uses `src/huey` as the canonical runtime package root.

## Canonical package areas

| Path | Purpose |
| --- | --- |
| `src/huey/core` | Core runtime and kernel-profile assets |
| `src/huey/platform` | Platform and installer support |
| `src/huey/connectors` | External integrations and connector-facing code |
| `src/huey/apps` | Application-level code |
| `src/huey/config` | Configuration templates and helpers |
| `src/huey/os` | Canonical HueyOS subsystem implementation |
| `src/huey/memory` | Preserved memory subsystem |

## Memory preservation

`src/huey/memory` is intentionally preserved. Layout migrations must not move it
without a separate architectural decision.

## Repository script areas

| Path | Purpose |
| --- | --- |
| `scripts/repo` | Repository guardrails, drift checks, and packaging helpers |
| `scripts/media` | Standalone media conversion utilities |
| `scripts/security` | Local developer security checks |
| `scripts/automation/py` | Curated Python launchers backed by `src/huey/memory/PY` |
| `scripts/automation/sh` | Shell wrappers backed by `src/huey/memory/SH` |
| `scripts/automation/bat` | Batch wrappers backed by `src/huey/memory/BAT` |
| `scripts/automation/ps1` | PowerShell wrappers backed by `src/huey/memory/PS1` |

Legacy flat paths under `scripts/` remain as compatibility wrappers where older tooling still references them directly.

`src/huey/platform/installers/windows/launcher` stores the safe Windows HueyOS launcher source and prebuilt executable used for local Command Center bootstrap and doctor checks.

## Canonical import path

New code should use:

```python
import huey.os
from huey.os import ...
```

## Compatibility window

The `hueyos` package remains temporarily available as a compatibility shim so
older imports continue to work during the migration window.

The shim should remain until code, tests, documentation, and downstream tooling
have moved to `huey.os`.

## Deferred work

The PyHuey / `pygpt-net` rename is intentionally deferred to the next migration
phase.
