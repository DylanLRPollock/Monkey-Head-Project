# Honeycomb Storage Operations

HueyOS stores long lived data inside a resilient honeycomb structure backed by
SQLite. This document explains how the new memory index, backup procedures,
monitoring, and retention policies work together to keep the hive healthy.

## Content-aware memory index

The honeycomb index maps high level content types (images, documents, logs,
telemetry sensor data, etc.) onto deterministic comb and cell prefixes. It uses
the existing auto-sort extension categories so the same heuristics drive both
filesystem organisation and database persistence.

| Content type | Honeycomb path prefix      | Auto-sort categories |
| ------------ | -------------------------- | -------------------- |
| Images       | `media/images/<cell>`      | JPEG, PNG            |
| Documents    | `knowledge/documents/<cell>` | PDF, MD, TXT, DOC, PPT, XLS |
| Logs         | `telemetry/logs/<cell>`    | LOG, JSON            |
| Sensor data  | `telemetry/sensor/<cell>`  | CSV, JSON            |
| Archives     | `packages/archives/<cell>` | ZIP, GZ              |
| Code         | `knowledge/code/<cell>`    | PY, SH               |

Developers interact with the index through
`monkey_head.honeycomb_index.HoneycombIndex`, which can classify a path and
store structured metadata alongside content-specific payloads. Custom content
mappings can be registered when new categories emerge, and all mappings are
returned via the API for introspection.

## Replication and backups

`monkey_head.honeycomb_backup.perform_rsync_snapshot` creates timestamped
snapshots of the memory directory using `rsync`. Snapshots may be sent to local
or remote (e.g. SSH mounted) destinations. Restoring a snapshot uses the same
utility via `restore_snapshot`.

Typical cron entry using a helper script:

```
0 * * * * hueyos /opt/hueyos/.venv/bin/python - <<'PY'
from pathlib import Path
from monkey_head.honeycomb_backup import perform_rsync_snapshot

perform_rsync_snapshot(destination=Path("/mnt/honeycomb-backups"))
PY
```

Restoration procedure:

1. Mount or attach the external media containing snapshots.
2. Choose the snapshot directory (e.g. `20240101-000000`).
3. Run `restore_snapshot(<snapshot>, <target>)` to repopulate the memory tree.
4. Restart services that rely on the honeycomb database.

If `rsync` is unavailable the helper raises a `BackupError`, ensuring operators
are alerted to missing tooling before an incident occurs.

## Monitoring honeycomb growth

`monkey_head.honeycomb_monitor.HoneycombMonitor` calculates per-comb usage,
content-type breakdowns, and growth trends (daily buckets). The data is
returned as JSON and feeds the new `/memory/honeycomb/usage` API endpoint.
Dashboard integrations can visualise the `summary`, `content_types`, and
`growth` arrays to highlight hot spots or unusually fast growth.

## Retention and pruning

`monkey_head.honeycomb_retention.RetentionPolicy` deletes stale records while
respecting critical data. Retention windows can be defined per content type
(using the index) or directly per comb, with durations specified as symbols
such as `14d` or `6m`. Applying a policy prunes cells older than the configured
thresholds and reports how many were removed, allowing automation to log and
alert on reclaimed capacity.

Combine backups, monitoring, and retention policies to maintain a resilient and
self-healing storage hive.
