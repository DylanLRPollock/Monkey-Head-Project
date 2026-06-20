# Dependency refresh notes

This change set resolves fixed-version Dependabot alerts, removes optional
no-fixed-version vulnerable packages from active root install surfaces, and
archives historical PyHuey freeze manifests so they are no longer treated as
live requirements files.

| Package or surface | Old version | New version or action | Manifest | Severity | Rationale | Classification |
| --- | --- | --- | --- | --- | --- | --- |
| `langsmith` | `0.8.3` | `0.8.18` | `requirements.txt` | high | GitHub lists a patched release; this package remains in the active baseline. | active root baseline |
| `langchain` | `1.2.18` | `1.3.9` | `requirements.txt` | medium | GitHub lists a patched release; update in place without broader dependency churn. | active root baseline |
| `pydantic-settings` | `2.14.1` | `2.14.2` | `pyproject.toml`, `requirements.txt`, `constraints.txt` | medium | Core runtime dependency pinned consistently across package metadata, full requirements, and constraints anchors. | direct runtime dependency |
| `pypdf` | `6.13.0` | `6.13.3` | `requirements.txt` | medium | GitHub lists a patched release; keep the reader dependency available in the full baseline. | active root baseline |
| `chromadb` | `1.5.9` | removed from active manifests | `requirements.txt`, `pyproject.toml` (`data` extra) | critical | No patched release is listed. Active code imports were not found in the V1 runtime surfaces audited for this refresh. | optional data stack removed from active surface |
| `chroma-hnswlib` | `0.7.6` | removed from active manifests | `requirements.txt`, `pyproject.toml` (`data` extra) | n/a | Companion package removed alongside `chromadb` to avoid leaving an orphaned optional vector-store pin in the active root surfaces. | optional data stack removed from active surface |
| `nltk` | `3.9.4` | removed from active root baseline | `requirements.txt` | high | No patched release is listed. The active package initializer probes for `nltk` defensively and tolerates it being absent. | optional package removed from active root surface |
| `torch` | `2.12.0` | removed from active manifests | `requirements.txt`, `constraints.txt`, `pyproject.toml` (`ml` extra) | low | No patched release is listed. The main runtime already falls back cleanly when the optional torch stack is unavailable. | optional ML stack removed from active surface |
| `torchaudio` | `2.11.0` | removed from active manifests | `requirements.txt`, `constraints.txt`, `pyproject.toml` (`ml` extra) | n/a | Removed with `torch` to keep the optional audio/vision stack internally consistent after dep-scoping the vulnerable torch surface. | optional ML stack removed from active surface |
| `torchvision` | `0.26.0` | removed from active manifests | `requirements.txt`, `constraints.txt`, `pyproject.toml` (`ml` extra) | n/a | Removed with `torch` to keep the optional audio/vision stack internally consistent after dep-scoping the vulnerable torch surface. | optional ML stack removed from active surface |
| historical PyHuey freeze snapshot | mixed | moved to `archives\dependency-snapshots\pyhuey-known-good-freeze.pip-snapshot` | `src\huey\platform\windows\huey\pyhuey\requirements-known-good-freeze.txt` | critical/high/low duplicates | Historical reference manifest only; archiving avoids treating stale snapshot pins as active install requirements. | archive-only reference |
| historical PyHuey freeze snapshot (redis) | mixed | moved to `archives\dependency-snapshots\pyhuey-known-good-with-redis-freeze.pip-snapshot` | `src\huey\platform\windows\huey\pyhuey\requirements-known-good-with-redis-freeze.txt` | critical/high/low duplicates | Historical reference manifest only; archiving avoids treating stale snapshot pins as active install requirements. | archive-only reference |
| `Twisted` | `25.5.0` | no version change; resolved by snapshot archival | archived PyHuey freeze snapshots | high | GitHub suggested `26.4.0rc2`, but these files are historical references and should not be updated to a release-candidate pin just to silence duplicate alerts. | archive-only reference |
| `Pygments` | `2.19.2` | no version change; resolved by snapshot archival | archived PyHuey freeze snapshots | low | Duplicate alert lived only in historical snapshots; no active runtime manifest retained the vulnerable pin. | archive-only reference |
