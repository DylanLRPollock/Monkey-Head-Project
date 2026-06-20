# HueyOS API reference

The FastAPI application in `huey.api:app` exposes HueyOS automation,
telemetry, and governance capabilities. The examples below assume the server is
running locally via `uvicorn huey.api:app --host 0.0.0.0 --port 1995 --reload` on port `1995`.

Each endpoint is grouped by tag and includes an example request with the shape
of the JSON response produced by the default in-memory fixtures.

## System

### `GET /healthz`
Lightweight readiness probe.

```bash
curl -s http://localhost:1995/healthz
```

```json
{"status": "ok", "service": "hueyos"}
```

### `GET /system/status` (alias: `GET /status/system`)
Returns host metrics, memory location, and OS details gathered by
`_build_system_status()`.【F:src/huey/api.py†L704-L756】【F:src/huey/api.py†L818-L832】

```bash
curl -s http://localhost:1995/system/status
```

```json
{
  "system": "Linux",
  "release": "6.6.0",
  "version": "#1 SMP PREEMPT_DYNAMIC",
  "architecture": "x86_64",
  "hostname": "huey-core",
  "python_version": "3.12.1",
  "cpu_count": 16,
  "memory_total": 34359738368,
  "memory_available": 30146560000,
  "uptime_seconds": 128734.42,
  "boot_time": 1705408000.0,
  "disk_free": 51234567890,
  "memory_path": "/opt/hueyos/memory"
}
```

## Task management

### `POST /tasks`
Submit a task to the cooperative scheduler.【F:src/huey/api.py†L832-L858】

```bash
curl -sX POST http://localhost:1995/tasks \
  -H 'Content-Type: application/json' \
  -d '{
    "command": "calibrate-lidar",
    "priority": 5,
    "requested_agent": "spark",
    "metadata": {"source": "ops-console"},
    "resource_profile": {"cpu": 0.5, "memory": 0.4, "battery": 0.2, "gpu": 0.1}
  }'
```

```json
{
  "task_id": "tsk_01HZYQ6BQJ6ZQK6J7P3Y4YV7H6",
  "command": "calibrate-lidar",
  "priority": 5,
  "requested_agent": "spark",
  "assigned_agent": "spark",
  "status": "queued",
  "created_at": 1705412345.123,
  "updated_at": 1705412345.123,
  "attempts": 0,
  "result": null,
  "error": null,
  "metadata": {"source": "ops-console"},
  "resource_profile": {"cpu": 0.5, "memory": 0.4, "battery": 0.2, "gpu": 0.1},
  "snapshot": {
    "timestamp": 1705412345.0,
    "cpu_percent": 18.2,
    "memory_available": 30146560000,
    "memory_total": 34359738368,
    "battery_percent": 82.4,
    "notes": "Nominal"
  },
  "history": [
    {"timestamp": 1705412345.123, "status": "queued", "message": "Task created"}
  ]
}
```

### `GET /tasks`
List scheduler tasks with optional `status` query filters.【F:src/huey/api.py†L858-L874】

```bash
curl -s 'http://localhost:1995/tasks?status=queued&status=running'
```

```json
{
  "tasks": [
    {"task_id": "tsk_01HZYQ6B…", "command": "calibrate-lidar", "status": "queued", "priority": 5,
     "requested_agent": "spark", "assigned_agent": "spark", "created_at": 1705412345.123,
     "updated_at": 1705412345.123, "attempts": 0, "result": null, "error": null,
     "metadata": {"source": "ops-console"},
     "resource_profile": {"cpu": 0.5, "memory": 0.4, "battery": 0.2, "gpu": 0.1},
     "snapshot": null,
     "history": [{"timestamp": 1705412345.123, "status": "queued", "message": "Task created"}]}
  ]
}
```

### `GET /tasks/{task_id}`
Retrieve a single task record.【F:src/huey/api.py†L874-L885】

```bash
curl -s http://localhost:1995/tasks/tsk_01HZYQ6BQJ6ZQK6J7P3Y4YV7H6
```

_Response identical to the submission payload above._

### `POST /tasks/{task_id}/cancel`
Cancel a pending or running task.【F:src/huey/api.py†L885-L898】

```bash
curl -sX POST http://localhost:1995/tasks/tsk_01HZYQ6B…/cancel
```

```json
{
  "task_id": "tsk_01HZYQ6B…",
  "status": "cancelled",
  "history": [
    {"timestamp": 1705412345.123, "status": "queued", "message": "Task created"},
    {"timestamp": 1705412400.456, "status": "cancelled", "message": "Operator requested cancellation"}
  ],
  "command": "calibrate-lidar",
  "priority": 5,
  "requested_agent": "spark",
  "assigned_agent": "spark",
  "created_at": 1705412345.123,
  "updated_at": 1705412400.456,
  "attempts": 0,
  "result": null,
  "error": null,
  "metadata": {"source": "ops-console"},
  "resource_profile": {"cpu": 0.5, "memory": 0.4, "battery": 0.2, "gpu": 0.1},
  "snapshot": null
}
```

## Sensors

### `GET /sensors/plugins`
Enumerate available sensor plugins and metadata.【F:src/huey/api.py†L904-L913】

```bash
curl -s http://localhost:1995/sensors/plugins
```

```json
{
  "plugins": ["dummy.temperature"],
  "metadata": [
    {
      "name": "dummy.temperature",
      "module": "huey.hardware.plugins.DummyTemperatureSensor",
      "description": "Simple example sensor returning a fixed temperature value.",
      "plugin": "dummy.temperature",
      "config_keys": ["baseline"]
    }
  ]
}
```

### `GET /sensors`
List configured sensor instances, including provenance and configuration.
【F:src/huey/api.py†L915-L930】

```bash
curl -s http://localhost:1995/sensors
```

```json
{
  "sensors": [
    {
      "name": "shop-temp-1",
      "plugin": "dummy.temperature",
      "module": "huey.hardware.plugins.DummyTemperatureSensor",
      "config": {"baseline": 21.0}
    }
  ]
}
```

### `POST /sensors/register`
Register a new sensor instance.【F:src/huey/api.py†L932-L956】

```bash
curl -sX POST http://localhost:1995/sensors/register \
  -H 'Content-Type: application/json' \
  -d '{"name": "ambient", "plugin": "dummy.temperature", "config": {"baseline": 19.5}}'
```

```json
{"name": "ambient", "plugin": "dummy.temperature", "config": {"baseline": 19.5}}
```

### `DELETE /sensors/{sensor_name}`
Remove a sensor instance from the manager.【F:src/huey/api.py†L958-L969】

```bash
curl -sX DELETE http://localhost:1995/sensors/ambient
```

```json
{"status": "removed", "sensor": "ambient"}
```

### `POST /sensors/{sensor_name}/poll`
Capture a fresh reading from a single sensor.【F:src/huey/api.py†L971-L989】

```bash
curl -sX POST http://localhost:1995/sensors/shop-temp-1/poll
```

```json
{
  "name": "shop-temp-1",
  "value": 21.0,
  "timestamp": 1705412450.321,
  "provenance": {
    "plugin": "dummy.temperature",
    "module": "huey.hardware.plugins.DummyTemperatureSensor",
    "config": {"baseline": 21.0}
  }
}
```

### `POST /sensors/poll`
Poll every configured sensor.【F:src/huey/api.py†L991-L998】

```bash
curl -sX POST http://localhost:1995/sensors/poll
```

```json
{
  "readings": [
    {
      "name": "shop-temp-1",
      "value": 21.0,
      "timestamp": 1705412450.321,
      "provenance": {
        "plugin": "dummy.temperature",
        "module": "huey.hardware.plugins.DummyTemperatureSensor",
        "config": {"baseline": 21.0}
      }
    }
  ]
}
```

### `GET /sensors/{sensor_name}/history`
Return honeycomb-backed history for a sensor.【F:src/huey/api.py†L1000-L1013】

```bash
curl -s 'http://localhost:1995/sensors/shop-temp-1/history?limit=3'
```

```json
{
  "sensor": "shop-temp-1",
  "readings": [
    {"name": "shop-temp-1", "value": 21.2, "timestamp": 1705412200.0,
     "provenance": {"plugin": "dummy.temperature", "module": "…", "config": {"baseline": 21.0}}},
    {"name": "shop-temp-1", "value": 21.0, "timestamp": 1705412300.0,
     "provenance": {"plugin": "dummy.temperature", "module": "…", "config": {"baseline": 21.0}}},
    {"name": "shop-temp-1", "value": 21.0, "timestamp": 1705412450.321,
     "provenance": {"plugin": "dummy.temperature", "module": "…", "config": {"baseline": 21.0}}}
  ]
}
```

### `GET /sensors/{sensor_name}/stream`
Server-sent events stream for a single sensor.【F:src/huey/api.py†L1015-L1025】

```bash
curl -N http://localhost:1995/sensors/shop-temp-1/stream
```

_Streamed lines in `data: {…}` format containing JSON readings._

### `GET /sensors/stream`
Server-sent events stream for all sensors.【F:src/huey/api.py†L1027-L1031】

```bash
curl -N http://localhost:1995/sensors/stream
```

## Network

### `GET /network/status`
Report connectivity status, interface inventory, and timestamps.【F:src/huey/api.py†L1033-L1040】

```bash
curl -s http://localhost:1995/network/status
```

```json
{
  "active_interface": "enp5s0",
  "interfaces": {
    "enp5s0": {"rssi": null, "throughput": 125.4},
    "wlp3s0": {"rssi": -48.0, "throughput": 72.1}
  },
  "wired_available": true,
  "wifi_available": true,
  "connected": true,
  "last_checked": 1705412405.987
}
```

### `POST /network/ensure`
Ensure wired connectivity with Wi-Fi failover.【F:src/huey/api.py†L1042-L1048】

```bash
curl -sX POST http://localhost:1995/network/ensure
```

```json
{
  "active_interface": "enp5s0",
  "interfaces": {
    "enp5s0": {"rssi": null, "throughput": 140.8},
    "wlp3s0": {"rssi": -50.0, "throughput": 68.4}
  },
  "wired_available": true,
  "wifi_available": true,
  "connected": true,
  "last_checked": 1705412406.112
}
```

## Power

### `GET /power/battery`
Expose current battery metrics.【F:src/huey/api.py†L1050-L1056】

```bash
curl -s http://localhost:1995/power/battery
```

```json
{
  "percent": 82.4,
  "secs_left": 5400.0,
  "power_plugged": true,
  "estimated_runtime_minutes": 135.0
}
```

### `GET /power/should-shutdown`
Report whether a safe shutdown is recommended.【F:src/huey/api.py†L1058-L1066】

```bash
curl -s http://localhost:1995/power/should-shutdown
```

```json
{"should_shutdown": false, "threshold": 0.15}
```

### `POST /power/shutdown`
Initiate a shutdown sequence via the battery monitor.【F:src/huey/api.py†L1068-L1074】

```bash
curl -sX POST http://localhost:1995/power/shutdown
```

```json
{
  "timestamp": 1705412500.512,
  "action": "shutdown-requested",
  "metadata": {"initiator": "operator", "method": "api"}
}
```

## Memory

### `GET /memory/pdfs`
List PDFs accessible to HueyOS, optionally scoping the search directory.【F:src/huey/api.py†L1109-L1121】

```bash
curl -s http://localhost:1995/memory/pdfs
```

```json
{
  "pdfs": ["governance-overview.pdf", "hardware-manual.pdf"],
  "directory": "/opt/hueyos/memory/DOCUMENTS"
}
```

### `GET /memory/pdfs/{filename}`
Resolve a filesystem path for a specific PDF.【F:src/huey/api.py†L1124-L1135】

```bash
curl -s http://localhost:1995/memory/pdfs/governance-overview.pdf
```

```json
{
  "filename": "governance-overview.pdf",
  "found": true,
  "path": "/opt/hueyos/memory/DOCUMENTS/governance-overview.pdf"
}
```

### `POST /memory/auto-sort`
Execute the auto-sort pipeline with optional dry-run support.【F:src/huey/api.py†L1138-L1155】

```bash
curl -sX POST http://localhost:1995/memory/auto-sort \
  -H 'Content-Type: application/json' \
  -d '{"source_dir": "memory/RAW", "destination_root": "memory", "dry_run": true}'
```

```json
{
  "source": "memory/RAW",
  "destination": "memory",
  "moved": ["memory/RAW/report.pdf -> memory/DOCUMENTS/report.pdf"],
  "skipped": ["memory/RAW/README.txt"]
}
```

### `GET /memory/honeycomb/usage`
Return aggregated honeycomb utilisation metrics produced by `HoneycombMonitor`.
【F:src/huey/api.py†L1158-L1185】

```bash
curl -s http://localhost:1995/memory/honeycomb/usage?window_days=14
```

```json
{
  "summary": [
    {"comb": "telemetry/sensor", "cells": 128, "payload_bytes": 24576,
     "oldest": 1703800000.0, "newest": 1705412400.0}
  ],
  "totals": {"cells": 512, "payload_bytes": 409600, "combs": 6, "last_update": 1705412400.0},
  "content_types": [
    {"content_type": "sensor", "cells": 256, "payload_bytes": 196608,
     "oldest": 1703800000.0, "newest": 1705412400.0}
  ],
  "growth": [
    {"date": "2025-01-14", "cells": 480},
    {"date": "2025-01-15", "cells": 512}
  ]
}
```

## AI tools

### `POST /ai/process-text`
Process text with `AIProcessor`, optionally streaming chunks.【F:src/huey/api.py†L1189-L1230】

```bash
curl -sX POST http://localhost:1995/ai/process-text \
  -H 'Content-Type: application/json' \
  -d '{"text": "HueyOS harmonises robotics and governance."}'
```

```json
{
  "processed_text": "[Processed] HueyOS harmonises robotics and governance."
}
```

Enable streaming with `?stream=true` to receive chunked responses.

### `POST /ai/compute-mean`
Return the arithmetic mean of supplied numbers.【F:src/huey/api.py†L1232-L1245】

```bash
curl -sX POST http://localhost:1995/ai/compute-mean \
  -H 'Content-Type: application/json' \
  -d '{"numbers": [18, 24, 42]}'
```

```json
{"mean": 28.0}
```

### `POST /ai/analyze-text`
Expose lightweight analytics generated by the AI processor.【F:src/huey/api.py†L1247-L1265】

```bash
curl -sX POST http://localhost:1995/ai/analyze-text \
  -H 'Content-Type: application/json' \
  -d '{"text": "Spark orchestrates collaborative autonomy."}'
```

```json
{
  "metrics": {
    "characters": 44,
    "words": 4,
    "lines": 1
  }
}
```

## Governance

### `GET /governance/emergency/status`
Snapshot of the emergency governance controller including approvals and managed
services.【F:src/huey/api.py†L1239-L1256】

```bash
curl -s http://localhost:1995/governance/emergency/status
```

```json
{
  "state": "normal",
  "active_since": null,
  "reason": null,
  "triggered_by": null,
  "approvals": [],
  "services": [
    {"name": "spark-agent", "essential": false, "managed": true},
    {"name": "zap-agent", "essential": false, "managed": true},
    {"name": "ollama", "essential": false, "managed": true}
  ]
}
```

### `POST /governance/emergency/enter`
Activate emergency mode once quorum requirements are met.【F:src/huey/api.py†L1260-L1277】

```bash
curl -sX POST http://localhost:1995/governance/emergency/enter \
  -H 'Content-Type: application/json' \
  -d '{
        "triggered_by": "spark",
        "reason": "Power instability",
        "approvals": ["volt", "watt"]
      }'
```

```json
{
  "state": "emergency",
  "active_since": 1705412505.221,
  "reason": "Power instability",
  "triggered_by": "spark",
  "approvals": ["spark", "volt", "watt"],
  "services": [
    {"name": "spark-agent", "essential": false, "managed": true},
    {"name": "zap-agent", "essential": false, "managed": true},
    {"name": "ollama", "essential": false, "managed": true}
  ]
}
```

### `POST /governance/emergency/exit`
Return to normal operations with the required approvals.【F:src/huey/api.py†L1280-L1295】

```bash
curl -sX POST http://localhost:1995/governance/emergency/exit \
  -H 'Content-Type: application/json' \
  -d '{"requested_by": "spark", "approvals": ["volt", "watt"]}'
```

```json
{
  "state": "normal",
  "active_since": null,
  "reason": null,
  "triggered_by": null,
  "approvals": [],
  "services": [
    {"name": "spark-agent", "essential": false, "managed": true},
    {"name": "zap-agent", "essential": false, "managed": true},
    {"name": "ollama", "essential": false, "managed": true}
  ]
}
```

### `POST /governance/emergency/action`
Validate a dual-authorised action during emergency mode.【F:src/huey/api.py†L1298-L1313】

```bash
curl -sX POST http://localhost:1995/governance/emergency/action \
  -H 'Content-Type: application/json' \
  -d '{"actor": "spark", "approvals": ["volt"], "action": "restart-reactor"}'
```

```json
{"status": "authorised", "action": "restart-reactor"}
```

## Administration

### `GET /admin/services`
Return service state tracked by `_SERVICE_STATES`.【F:src/huey/api.py†L1316-L1321】

```bash
curl -s http://localhost:1995/admin/services
```

```json
{
  "services": [
    {"name": "spark-agent", "status": "running", "last_changed": 1705412000.0},
    {"name": "zap-agent", "status": "stopped", "last_changed": 1705412100.0}
  ]
}
```

### `POST /admin/services/{service_name}/start`
Mark a service as running.【F:src/huey/api.py†L1323-L1332】

```bash
curl -sX POST http://localhost:1995/admin/services/zap-agent/start
```

```json
{"name": "zap-agent", "status": "running", "last_changed": 1705412508.443}
```

### `POST /admin/services/{service_name}/stop`
Mark a service as stopped.【F:src/huey/api.py†L1335-L1344】

```bash
curl -sX POST http://localhost:1995/admin/services/zap-agent/stop
```

```json
{"name": "zap-agent", "status": "stopped", "last_changed": 1705412510.112}
```

### `POST /admin/system-check`
Run the full system check suite and return pass/fail information.【F:src/huey/api.py†L1346-L1354】

```bash
curl -sX POST http://localhost:1995/admin/system-check
```

```json
{
  "results": {"python_version": true, "gpu_driver": true, "disk_space": true},
  "passed": true
}
```

### `POST /admin/health-check`
Delegate to the `/healthz` endpoint for administrative contexts.【F:src/huey/api.py†L1356-L1360】

```bash
curl -sX POST http://localhost:1995/admin/health-check
```

```json
{"status": "ok", "service": "hueyos"}
```

## Resilience

### `GET /resilience/monitors`
List monitored processes and their health metadata.【F:src/huey/api.py†L1035-L1044】

```bash
curl -s http://localhost:1995/resilience/monitors
```

```json
[
  {
    "name": "ollama",
    "healthy": true,
    "auto_restart": true,
    "last_heartbeat": 1705412300.0,
    "last_restart": null,
    "restart_attempts": 0,
    "manual_override_reason": null
  }
]
```

### `POST /resilience/monitors/{name}/override`
Toggle automatic restarts for a monitored process.【F:src/huey/api.py†L1046-L1060】

```bash
curl -sX POST http://localhost:1995/resilience/monitors/ollama/override \
  -H 'Content-Type: application/json' \
  -d '{"auto_restart": false, "reason": "maintenance"}'
```

```json
{
  "name": "ollama",
  "healthy": true,
  "auto_restart": false,
  "last_heartbeat": 1705412300.0,
  "last_restart": null,
  "restart_attempts": 0,
  "manual_override_reason": "maintenance"
}
```

### `POST /resilience/monitors/{name}/restart`
Force a manual restart, regardless of override state.【F:src/huey/api.py†L1063-L1075】

```bash
curl -sX POST http://localhost:1995/resilience/monitors/ollama/restart
```

```json
{
  "name": "ollama",
  "healthy": true,
  "auto_restart": false,
  "last_heartbeat": 1705412305.512,
  "last_restart": 1705412305.512,
  "restart_attempts": 1,
  "manual_override_reason": "maintenance"
}
```

### `POST /resilience/poll`
Return crash events detected since the previous poll.【F:src/huey/api.py†L1078-L1096】

```bash
curl -sX POST http://localhost:1995/resilience/poll
```

```json
{
  "events": [
    {
      "process": "ollama",
      "timestamp": 1705412350.432,
      "restarted": true,
      "message": "Process restarted after crash",
      "metadata": {}
    }
  ]
}
```

### `POST /resilience/watchdog/ping`
Send a heartbeat to the systemd watchdog client.【F:src/huey/api.py†L1099-L1106】

```bash
curl -sX POST http://localhost:1995/resilience/watchdog/ping
```

```json
{"watchdog": true}
```
