# Legacy Python consolidation — review plan (2026-11-02)

The repository retains 144 Python files under src/huey/memory/PY,
mixing production logic, executable scripts, tests, examples and wrappers.
The supplied ZIP matches those names and sizes; representative Git blob
hashes also match. The 144 files parse on Python 3.13, but parsing
does not establish that they work or that they are safe to remove.

## Migration matrix

| Current functions | Canonical owner | Gate |
|---|---|---|
| API, AI processor, LLM | huey.os.api, huey.ai and connectors | auth, endpoint, provider tests |
| GUI, dashboard | huey.gui and huey.apps | startup and headless tests |
| Memory ingestion, indexing, metadata | huey.memory | schema, persistence, recovery |
| Honeycomb, backups | huey.honeycomb and huey.storage | atomic writes, restore |
| Speech, FFmpeg, media | huey.media | fixtures and failure coverage |
| PyHuey manifests | huey.connectors.pyhuey | bounded tool permissions |
| V1 proof, fixtures, response logging | huey.v1 | offline deterministic tests |
| Repo scanners | scripts/repo | exit codes and CI checks |
| Installers, apt sources, system updates | huey.platform and scripts/platform | explicit opt-in, rollback |
| test_*, conftest | tests | preserve unique assertions |
| example_* and demos | examples | document dependencies |
| Temporary prototypes | quarantine pending usage evidence | no deletion without audit |

## First implemented slice

The three media CLI implementations move to the canonical huey.media
package as cli_ffmpeg_check, cli_audio_prepare, and cli_probe. Existing
huey.memory.PY imports become aliases to the canonical modules, preserving
monkeypatch behavior and import identity. scripts/*.py operator wrappers
restore paths required by the current PyHuey bridge.

The tool manifest is promoted to huey.connectors.pyhuey.tool_manifest;
its commands use installed Python module paths. Preparing audio is
a mutating, deferred capability and never an arbitrary-shell tool.

## Requirements before subsequent moves

1. Inventory static and dynamic imports; a zero reference count does not
   establish that a module is unused.
2. Keep imports compatible while promoting code one domain at a time.
3. Test behavior on Python 3.13; Python 3.14 remains experimental only.
4. Run API, GUI, Command Center, PyHuey, memory and V1 integration tests.
5. Scan new code with Bandit, Ruff and CodeQL; block implicit filesystem,
   package-manager, hardware or network changes.
6. Remove legacy adapters only in a later change after runtime validation.

## Proposed CLI design, not yet implemented

- huey diagnostics --json: system, GPU and FFmpeg readiness
- huey memory index --root PATH --dry-run: controlled indexing
- huey v1 prove --fixture ID: offline proof runs
- huey storage verify --no-write: integrity and restore checks
- huey pyhuey tools list: capabilities and restrictions

Further domains should not be activated merely because they are present
in the memory directory. Registered and tested interfaces are required.
