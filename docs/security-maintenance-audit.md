# Security & Maintenance Audit (2026-03-12)

This audit summarizes high-priority fixes to reduce security risk and keep the
repository operationally up to date.

## High priority (fix first)

1. **Add API authentication/authorization controls**
   - The FastAPI control surface exposes administration, governance,
     resilience, and automation endpoints without request-level authn/authz
     dependencies.
   - Affected examples include:
     - `POST /admin/system-check`
     - `POST /admin/services/{service_name}/start`
     - `POST /admin/services/{service_name}/stop`
     - `POST /governance/emergency/*`
   - Recommendation:
     - Introduce bearer-token or mTLS auth for all non-health endpoints.
     - Add role-based guards (operator/admin/governance).
     - Restrict dangerous routes to localhost or private networks by default.

2. **Resolve Python runtime baseline drift**
   - Packaging requires Python `>=3.13,<3.15`.
   - Contributor docs specify Python `3.14.x`.
   - Docker Compose currently builds with `3.11-slim` by default.
   - Recommendation:
     - Set Compose default to a supported runtime (3.13/3.14).
     - Align README/CONTRIBUTING/compose defaults with one canonical baseline.

3. **Fix console-script entrypoint mismatch**
   - `pyproject.toml` maps `huey-api = "huey.api:main"`.
   - `src/huey/api.py` is a compatibility wrapper exporting the module object
     and does not define `main`.
   - Recommendation:
     - Add a `main()` function in `huey.api` (uvicorn launcher), or
     - Point script to an existing callable.

## Medium priority

4. **Reduce optional broad exception handling where possible**
   - Several modules intentionally catch broad `Exception` during optional
     imports/telemetry collection. This is acceptable for compatibility but can
     mask unexpected errors in production.
   - Recommendation:
     - Narrow exceptions where feasible and emit structured logs/metrics.

5. **Add dependency vulnerability scanning to CI**
   - Recommendation:
     - Add `pip-audit` (or `safety`) in CI for base + selected extras.
     - Fail builds on known critical vulnerabilities.

6. **Harden deployment defaults**
   - Compose binds API to `0.0.0.0` and mounts host memory/config by default.
   - Recommendation:
     - Provide secure production profile with:
       - private network binding,
       - read-only mounts where possible,
       - auth required,
       - optional reverse-proxy/TLS guidance.

## Suggested implementation order

1. Authn/authz middleware + route protections.
2. Runtime-version alignment (pyproject/docs/compose).
3. Script entrypoint fix for `huey-api`.
4. CI security scanning + dependency policy.
5. Deployment hardening profile and docs.
