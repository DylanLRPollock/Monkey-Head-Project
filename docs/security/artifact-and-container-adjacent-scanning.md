# Artifact and Container-Adjacent Scanning

This repository includes a GitHub Actions workflow at:

- `.github/workflows/security-artifact-container-scan.yml`

## What it checks

1. **Large and binary-adjacent tracked files**
   - Enumerates tracked files via `git ls-files`.
   - Produces a size-ranked report and marks files with binary-like extensions (for example `.deb`, `.iso`, `.zip`, `.so`).

2. **Trivy filesystem scan (optional/non-blocking baseline)**
   - Runs `trivy fs` against the repository filesystem only.
   - Includes vulnerability, secret, and misconfiguration scanners.
   - Scoped to local repo content only; no external systems are scanned.

## Artifacts produced

- `artifact-risk-scan-results`
  - `large-files-report.md`
  - `large-files-top200.json`
- `trivy-fs-scan-results`
  - `trivy-fs.sarif` (if produced)
  - `trivy-status.md`

## How to interpret results

- Large-file findings are **triage signals**, not automatic failures.
- Binary-like extension flags indicate assets that may need policy review (for provenance, licensing, and supply-chain exposure).
- Trivy findings at this stage are **non-blocking** to establish visibility first.
- Prioritize:
  1. Confirm whether flagged artifacts are expected release assets.
  2. Investigate any CRITICAL/HIGH items with clear package/file attribution.
  3. Tighten policy later by adding blocking thresholds once false positives are understood.

## Safety constraints

- Do not upload secrets to artifacts.
- The workflow scans repository contents only.
- No external hosts or systems are scanned by this workflow.
