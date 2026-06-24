# Huey Tools plugin

Huey Tools is a safe PyHuey-side bridge for selected HueyOS / Monkey-Head-Project functions.

## What it does

- reports bridge and safety status
- validates FFmpeg readiness through a fixed wrapper
- prepares audio for transcription through the Huey speech pipeline
- probes media metadata through a fixed wrapper
- lists supported and planned Huey tool groups
- generates implementation prompts for known Huey task IDs

## Configuration

Use environment variables for this bridge:

- `HUEY_MONKEY_HEAD_PROJECT_PATH`
- `HUEY_PYTHON_EXECUTABLE`
- `HUEY_TOOLS_TIMEOUT_SECONDS`
- `HUEY_TOOLS_ALLOW_EXTERNAL_PATHS`
- `HUEY_TOOLS_ALLOWED_WORKSPACE_ROOTS`

`HUEY_MONKEY_HEAD_PROJECT_PATH` should point at a local Monkey-Head-Project checkout. The bridge does not hardcode a repository path.

## Supported commands

- `huey_status`
- `huey_ffmpeg_check`
- `huey_prepare_audio`
- `huey_probe_media`
- `huey_list_tools`
- `huey_generate_task_prompt`
- `huey_safety_policy`

## Safety policy

Allowed by default:

- status/reporting
- FFmpeg validation
- audio preparation
- media probing
- tool listing
- task prompt generation
- safety policy inspection

Blocked by default:

- arbitrary shell execution
- git commit/push
- repository mutation
- file deletion
- hardware/servo/motor control
- power actions
- governance mutation
- memory mutation
- network mutation
- overwrite operations unless explicitly allowed later

## FFmpeg check workflow

The bridge calls the fixed wrapper:

- `scripts/check_ffmpeg_environment.py --json`

It does not build arbitrary FFmpeg commands from model input.

## Audio preparation workflow

The bridge calls the fixed wrapper:

- `scripts/prepare_audio_for_transcription.py SOURCE --json`

Optional flags:

- `--output`
- `--output-dir`
- `--manifest`
- `--overwrite`

Overwrite is blocked by default at the plugin safety layer.

JSON output includes the prepared output path plus a structured manifest with
input, processing steps, toolchain, and output-contract metadata.

## Intentionally blocked

This bridge does **not** provide:

- hardware control
- power control
- firmware flashing
- governance mutation
- memory mutation
- arbitrary command execution
- direct file deletion
- direct git mutation

## Future work

- Command Center embedding
- broader runtime orchestration
- simulation-first hardware tooling
- governance mock integrations
- eventual PyHuey package rename planning
