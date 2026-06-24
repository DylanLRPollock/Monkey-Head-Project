# Huey Brain V1 Setup Runbook (Legion Go Boundary)

## Scope and boundary

- This runbook is for **Huey Brain V1** on the **Lenovo Legion Go** boundary only.
- V1 proof loop target in this repository is:
  **controlled MP3 fixture → source probe / audio prep → local transcription stub/mock path → cognition bridge stub/mock path → structured log**.
- This runbook does **not** enable or claim live microphone ingestion, wake-word, or Huey Body integration.

## Target OS note (Debian / Forky)

- Use a Debian-family Linux target appropriate for the current HueyOS stabilization direction.
- If your Legion Go host is on a Debian "Forky" path, keep this runbook as a conservative baseline and pin package decisions per your host policy.
- All commands below assume a Debian-family package manager (`apt`).

## 1) Python 3.13 setup

```bash
python3.13 --version
```

If missing:

```bash
sudo apt update
sudo apt install -y python3.13 python3.13-venv python3.13-dev
```

Re-check:

```bash
python3.13 --version
```

## 2) Create and activate virtualenv

From repository root:

```bash
cd /path/to/Monkey-Head-Project
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

## 3) Install ffmpeg

```bash
sudo apt install -y ffmpeg
ffmpeg -version
```

> Note: the mock V1 path below does not decode real audio, but `ffmpeg` is included because it is part of expected audio tooling for future real transcription wiring.

## 4) Install project

Editable install from repo root:

```bash
python -m pip install -e .
```

Optional dependency sanity check:

```bash
pip check
```

## 5) Fixture directory layout (controlled inputs)

Create a deterministic local fixture layout:

```bash
mkdir -p fixtures/v1/incoming fixtures/v1/processed fixtures/v1/failed runs
```

Recommended conventions:

- `fixtures/v1/incoming/` → queued controlled fixture files
- `fixtures/v1/processed/` → archived after successful queue runs
- `fixtures/v1/failed/` → failed fixtures and sidecar reason files
- `runs/` → structured output logs

For single-run mock smoke tests, create a placeholder MP3 fixture path:

```bash
touch fixtures/v1/incoming/mock_fixture.mp3
```

### Audio preparation wrapper

This fixed wrapper is the current safe way to inspect and prepare a fixture
before transcription:

```bash
python scripts/prepare_audio_for_transcription.py fixtures/v1/incoming/mock_fixture.mp3 --json
```

Useful flags:

- `--output`
- `--output-dir`
- `--manifest`
- `--overwrite`

Expected result:

- emits a prepared mono 16 kHz WAV path
- returns structured manifest JSON including input, stages, and tool metadata
- keeps the original fixture intact

## 6) Mock V1 run command (implemented path)

This is the executable CI-safe path currently available:

```bash
huey v1-run fixtures/v1/incoming/mock_fixture.mp3 --mock --log-dir runs
```

Expected behavior:

- command exits successfully
- prints JSON containing `log_file` and `run_id`
- appends one JSON line record to `runs/v1-run.jsonl`

Quick verification:

```bash
tail -n 1 runs/v1-run.jsonl
```

## 7) Structured log location

Primary log artifact for `v1-run`:

- `runs/v1-run.jsonl`

Queue mode (`v1-run-queue`) writes per-fixture JSON logs to the directory supplied via `--log-dir`.

## 8) Real transcription path (placeholder, not implemented here)

> **Status: NOT IMPLEMENTED IN THIS RUNBOOK**

Current CLI behavior requires `--mock` by default and explicitly blocks real provider flow unless custom provider wiring is added in code/runtime configuration.

Future work item (not part of this runbook):

- wire a real local transcription function and real cognition bridge provider
- preserve the same V1 structured log contract
- keep fixture-first deterministic input semantics for proofability

## 9) SSH ingress note (operator access)

SSH is an ingress/operations mechanism only; it does not change V1 boundaries.

Typical ingress pattern:

```bash
ssh <user>@<legion-go-host>
```

Recommended operational posture:

- use key-based auth
- restrict users/groups
- keep run artifacts under controlled directories (`fixtures/`, `runs/`)
- perform V1 commands directly on the Legion Go host to preserve locality
