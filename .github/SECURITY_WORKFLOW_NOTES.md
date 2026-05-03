# GitHub Actions Security Workflow Notes

## Policy
- Prefer immutable action references pinned to full commit SHAs.
- Track the upstream major tag in a trailing comment (for example `# v6`) to preserve upgrade intent.
- Default workflow token permissions to least privilege (`contents: read`) and only add write scopes when required by a job.
- Keep behavior changes out of hardening-only updates; only action pinning and permission minimization are in scope.

## Reviewed action pins
- `actions/checkout` pinned to commit `de0fac2e4500dabe0009e67214ff5f5447ce83dd` (upstream `v6`).
- `actions/setup-python` pinned to commit `a309ff8b426b58ec0e2a45f0f869d46889d02405` (upstream `v6`).
- `actions/upload-artifact` pinned to commit `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` (upstream `v7`).
- `github/codeql-action` (`init`, `analyze`) pinned to commit `ed410739ba306e4ebe5e123421a6bd694e494a2b` (upstream `v4`).

## Permission baseline
- Workflow-level `permissions: contents: read` is preferred.
- CodeQL keeps additional permissions required to upload analysis (`security-events: write`) and read packages/actions where needed.
