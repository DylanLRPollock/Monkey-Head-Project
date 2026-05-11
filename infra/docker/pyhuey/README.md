# PyHuey optional cockpit image

This directory defines an **optional PyHuey cockpit/tooling container image** for
Monkey-Head-Project. It is intentionally separate from the HueyOS runtime image.

## Scope boundary

- **HueyOS runtime**: `infra/docker/Dockerfile` (runs `huey-api`).
- **PyHuey cockpit/tooling**: `infra/docker/pyhuey/Dockerfile` (derived from
  upstream `pygpt-net` for provenance and compatibility).

PyHuey is a project-controlled cockpit/tooling integration surface and **not**
the Huey Brain V1 runtime boundary.

## Provenance

PyHuey cockpit packaging here preserves upstream PyGPT provenance by installing
`pygpt-net` and retaining the upstream `pygpt` entrypoint for compatibility.
