# Repository Alignment Pass

## Goal

Update old or unaligned project files so the repository reflects the current Monkey-Head-Project / HueyOS / PyHuey direction.

## Current direction

- HueyOS is the project-facing operating/runtime layer.
- PyHuey is the Windows 11 / Python 3.13 PyGPT-derived interface.
- Docker is optional development/sandbox infrastructure unless explicitly promoted.
- Kubernetes is not active infrastructure unless live manifests or deployment files prove otherwise.
- Archived memory, OLD prompts, and historical notes should not be rewritten as if they are current docs.

## File buckets

### Update in place

Files that are active and should reflect current project reality.

### Mark optional / legacy

Files that may still be useful but should not be presented as the primary runtime path.

### Archive / leave untouched

Historical files, old prompts, memory snapshots, and preserved project history.

### Delete candidates

Files that are duplicated, broken, unused, and not useful as historical artifacts.

## Notes

This pass should prefer small, reviewable commits.
