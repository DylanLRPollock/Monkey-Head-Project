# Legacy root wrapper cleanup

This note records the first layout-standardization cleanup after the generated-artifact and salvage branches were merged.

## Decision

The repository should keep importable Python source under `src/huey` and avoid maintaining duplicate root-level package wrappers such as `huey/...` and `hueyos/...`.

The following root wrappers were removed because each only re-exported the canonical implementation already present under `src/huey/memory/PY`:

- `huey/memory/PY/error_handler.py`
- `hueyos/convert_mkv_to_mp4.py`
- `hueyos/convert_pdf_to_text.py`
- `hueyos/convert_video_to_gif.py`
- `hueyos/media_conversion.py`

## Canonical locations

Use these source modules instead:

- `src/huey/memory/PY/error_handler.py`
- `src/huey/memory/PY/convert_mkv_to_mp4.py`
- `src/huey/memory/PY/convert_pdf_to_text.py`
- `src/huey/memory/PY/convert_video_to_gif.py`
- `src/huey/memory/PY/media_conversion.py`

## Rationale

Keeping duplicate root wrappers makes the checkout harder to reason about and risks shadowing the editable `src` package layout. The standardized project layout is:

```text
src/huey/                 canonical Huey source
src/huey/os/              HueyOS layer
src/huey/connectors/      external and companion integrations
src/huey/media/           media and FFmpeg pipeline code
src/huey/memory/          memory system code
scripts/                  operator/developer entry points
integrations/             companion applications and dashboards
docs/                     project and developer documentation
```

Compatibility should be added intentionally through documented adapters or console entry points, not through duplicate root package files.
