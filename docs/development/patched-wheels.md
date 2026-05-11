# Patched wheels policy (PyHuey Redis overlay)

This document defines how to use and audit locally patched wheels without making normal installs depend on local machine paths.

## Scope

- `requirements.txt` remains the portable baseline install for the repository.
- Patched wheel overlays are optional and must be explicitly applied.
- No absolute local user path (for example `C:\\Users\\...`) may be required for standard installs.

## Current wheelhouse entry

| Field | Value |
|---|---|
| Wheel filename | `llama_index_vector_stores_redis-0.8.0-py3-none-any.whl` |
| SHA256 hash | `2a09961603a50f9148b4632e6d40abb23b990f35df0f530f33a7c710625cf31a` |
| Source version | `llama-index-vector-stores-redis==0.8.0` |
| Patch reason | Temporary Redis vector-store compatibility overlay for PyHuey Windows cockpit environment. |
| Wheel path in repo | `platform/windows/huey/pyhuey/patched-wheels/` |
| Install command | `python -m pip install "llama-index-vector-stores-redis @ ./platform/windows/huey/pyhuey/patched-wheels/llama_index_vector_stores_redis-0.8.0-py3-none-any.whl#sha256=2a09961603a50f9148b4632e6d40abb23b990f35df0f530f33a7c710625cf31a"` |
| Rollback path | `python -m pip uninstall -y llama-index-vector-stores-redis && python -m pip install "llama-index-vector-stores-redis==0.8.0"` |

## Validation note (`pip check`)

After applying either:

- baseline install (`python -m pip install -r requirements.txt`), or
- the optional patched wheel overlay,

run:

```bash
python -m pip check
```

Expected outcome is:

```text
No broken requirements found.
```

If `pip check` fails after overlay install, remove the overlay via the rollback path above and re-run `python -m pip check`.
