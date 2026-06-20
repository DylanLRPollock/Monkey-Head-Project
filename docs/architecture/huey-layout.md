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
