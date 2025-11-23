# Honeycomb Storage Operations

HueyOS stores long-lived data inside a resilient honeycomb structure backed by
SQLite. The honeycomb abstracts the storage of telemetry, documents, and other
payloads into **combs** (namespaces) and **cells** (individual records). This
section explains how the storage layer is implemented, how it interacts with the
sensor manager, and which tooling is available for monitoring, backups, and
retention.

## Storage model

The `huey.honeycomb.storage.HoneycombStorage` class exposes a key/value API that
persists JSON payloads into the `honeycomb_cells` table.【F:src/huey/honeycomb/storage.py†L34-L155】
Keys are split on `/` to derive comb and cell components, enabling structured
queries and efficient indices. Examples:

| Key example                                | Comb                    | Purpose                              |
|--------------------------------------------|-------------------------|--------------------------------------|
| `telemetry/sensor/air_quality/8fa3…`       | `telemetry/sensor`      | Real-time sensor readings            |
| `knowledge/documents/design/v1`            | `knowledge/documents`   | Indexed project documents            |
| `media/images/20250201-capture01`          | `media/images`          | Archived camera stills               |

`HoneycombStorage.store()` automatically timestamps inserts and performs an
upsert so updates preserve the original creation timestamp while refreshing the
`updated_at` column.【F:src/huey/honeycomb/storage.py†L116-L140】 The helper methods
`load()`, `get_record()`, `list_keys()`, `remove()`, and `count()` make the
storage behave like a persistent dictionary with optional prefix scoping.【F:src/huey/honeycomb/storage.py†L143-L199】

## Integration with the sensor manager

`sensor_manager.SensorManager` captures readings from registered plugins and
immediately persists them into the honeycomb. Each reading is given a unique
cell name derived from a UUID, ensuring durable histories for later analysis.
【F:src/huey/hardware/manager.py†L43-L156】 The same manager exposes streaming queues
and history loaders so operators can replay sensor activity or subscribe to live
feeds without touching the underlying database.

When writing your own sensor plugin, no special code is required to talk to the
honeycomb. Calling `SensorManager.poll_sensor()` or `poll_all()` records the
reading and broadcasts it to subscribers.

## Querying and analytics

Several utilities build on top of the storage abstraction:

- `HoneycombIndex` classifies filesystem artefacts into comb paths based on
  content type mappings shared with the auto-sorter.【F:src/huey/honeycomb/index.py†L20-L198】
- `HoneycombMonitor.build_usage_report()` aggregates totals, content-type
  breakdowns, and growth samples. The FastAPI endpoint `/memory/honeycomb/usage`
  returns this data in the `HoneycombUsageResponse` schema for dashboards or
  alerting pipelines.【F:src/huey/honeycomb/monitor.py†L27-L114】【F:src/huey/api.py†L1650-L1678】
- `SensorManager.load_history()` retrieves ordered historical records for a
  sensor, relying on `HoneycombStorage.list_keys()` and `get_record()` to load
  payloads and timestamps.【F:src/huey/hardware/manager.py†L113-L155】

## Backups and replication

`huey.honeycomb.backup.perform_rsync_snapshot` creates timestamped snapshots of
`memory/` using `rsync`. Snapshots may be sent to local or remote destinations,
and `restore_snapshot` rehydrates the tree when needed. A sample cron entry:

```
0 * * * * hueyos /opt/hueyos/.venv/bin/python - <<'PY'
from pathlib import Path
from huey.honeycomb.backup import perform_rsync_snapshot

perform_rsync_snapshot(destination=Path("/mnt/honeycomb-backups"))
PY
```

Always verify `rsync` availability during commissioning so operators are alerted
if the backup toolchain is missing.

## Monitoring growth

`HoneycombMonitor` calculates per-comb utilisation, content-type totals, and a
rolling growth series (daily buckets by default). The resulting payload feeds
Grafana or similar dashboards so sudden spikes become visible. Combine it with
`HoneycombIndex` to align storage reporting with the auto-sort file taxonomy.
【F:src/huey/honeycomb/monitor.py†L27-L108】

## Retention and pruning

`huey.honeycomb.retention.RetentionPolicy` applies content-aware expiry rules to
old cells, using duration strings such as `14d` or `6m`. Operators can set
different windows per content type or comb and record how many rows were
pruned, closing the loop between ingestion, monitoring, and retention.【F:src/huey/honeycomb/retention.py†L29-L95】
