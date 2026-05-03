# SECURITY INVENTORY (Read-only pass)

## Confirmed files inspected
- Dependency manifests: `requirements.txt`, `constraints.txt`, `infra/docker/docker/subos/requirements.txt`, `infra/docker/docker/hostos/requirements.txt`, `infra/docker/docker/nanoos/requirements.txt`.
- Dockerfiles: `infra/docker/Dockerfile`, `infra/docker/Dockerfile.vnc`, `infra/docker/docker/Dockerfile`, `infra/docker/docker/pygpt/Dockerfile`, `infra/docker/docker/subos/Dockerfile`, `infra/docker/docker/hostos/Dockerfile`, `infra/docker/docker/nanoos/Dockerfile`, `src/huey/memory/DOCKER/Dockerfile`, `src/huey/memory/DOCKER/Dockerfile.vnc`.
- Compose files: `infra/docker/docker-compose.yml`, `infra/docker/docker/docker-compose.yml`, `src/huey/memory/YML/docker-compose.yml`, `src/huey/memory/YAML/compose-dev.yaml`.
- GitHub automation/security: `.github/workflows/ci.yml`, `.github/workflows/codeql.yml`, `.github/dependabot.yml`.
- Env/secrets examples: `huey.env.example`, `infra/secrets/README.md`, `infra/secrets/huey-key-example`.
- Command execution and scheduler-related code paths: `src/huey/memory/PY/api.py`, `src/huey/memory/PY/dashboard.py`, `src/huey/pygpt_net/tools/manager/__init__.py`, `src/huey/services/container_management.py`, `infra/docker/docker/orchestrator_utils.py`, plus supporting scripts under `scripts/`.

## Hardcoded credential findings
- No confirmed active hardcoded API keys/tokens found in inspected scope.
- `huey.env.example` includes empty placeholders (`OPENAI_API_KEY=`, `GOOGLE_API_KEY=`, `ANTHROPIC_API_KEY=`, `OPENROUTER_API_KEY=`, `HUEY_API_TOKEN=`), which is appropriate for templates.
- `infra/secrets/huey-key-example` is a non-secret placeholder text file, not key material.

## Docker image pinning findings
- Multiple images are not digest-pinned (e.g., `python:${PYTHON_VERSION}`, `redis:7-alpine`, and internal tags like `hueyos:latest`), which weakens supply-chain immutability.
- Some Dockerfiles pull mutable apt package indexes at build time without snapshot pinning.

## Exposed service/port findings
- `infra/docker/docker-compose.yml` publishes API/VNC-facing port `1995` and binds to loopback by default (`127.0.0.1`), which is good baseline hardening.
- `infra/docker/Dockerfile.vnc` exposes `1995`; noVNC depends on runtime password env var (`VNC_PASSWORD`) and exits when absent.
- Redis in compose is profile-gated (`extras`) and not directly host-published in inspected compose.

## Auth/token enforcement findings
- API middleware enforces bearer-token auth when `HUEY_API_TOKEN` is set; only `/healthz` is public.
- If `HUEY_API_TOKEN` is unset/empty, API auth is effectively disabled (by design), which is a deployment risk in non-local environments.

## Command execution surface findings
- Subprocess surfaces are extensive across orchestration and utilities (docker, kubectl, systemctl, apt, ufw, shell scripts).
- Task dashboard accepts free-text command submissions into scheduler records; this is a sensitive pathway that should be treated as privileged operator input.
- Most subprocess calls use argument lists (better than shell-string execution), and no high-signal `shell=True` usage was confirmed in inspected scope.

## Dependency scanning gaps
- CodeQL is configured (weekly + PR/push to main) and Dependabot is enabled for pip/actions.
- No dedicated dependency-vulnerability job was confirmed in CI (e.g., `pip-audit`, `safety`, `osv-scanner`) to fail PRs on known CVEs.
- No SBOM generation/attestation step was confirmed for container or Python artifacts.

## Recommended remediation order
1. **Enforce production auth defaults**: require non-empty `HUEY_API_TOKEN` outside development; fail fast if missing.
2. **Reduce command-execution risk**: gate scheduler/task command inputs behind strict RBAC/allowlists and audit logging.
3. **Strengthen container supply chain**: pin base images by digest and use reproducible apt sources/snapshots.
4. **Add CI vulnerability gates**: integrate `pip-audit`/OSV and container image scanning (e.g., Trivy/Grype) with fail thresholds.
5. **Add SBOM + provenance**: generate CycloneDX/SPDX and attach build attestations.
6. **Harden compose defaults**: keep loopback binds, avoid `latest` tags, and document secure overrides for remote deployments.
