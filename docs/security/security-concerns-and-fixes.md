# Security Concerns and Fixes

Updated: 2026-04-29

## Fixed in this pass

1. **Committed private-key material**
   - Concern: `infra/secrets/huey-key-example` contained OpenSSH private-key
     material, which can train contributors to commit real keys and may trigger
     secret scanners.
   - Fix: Replaced it with a non-secret placeholder, added
     `infra/secrets/README.md`, ignored generated secret files, and excluded
     `infra/secrets/` from Docker build contexts.
   - Follow-up: If the old key was ever used, rotate it.

2. **Unauthenticated API control surface**
   - Concern: HueyOS exposes system, governance, resilience, power, network, and
     admin endpoints. These are high-risk if the API is reachable by anything
     other than trusted local tooling.
   - Fix: Added optional bearer-token middleware. Set `HUEY_API_TOKEN` to require
     `Authorization: Bearer <token>` on every endpoint except `/healthz`.
   - Follow-up: Add role-based authorization for operator/admin/governance
     actions.

3. **Network services bound too broadly by default**
   - Concern: Local server defaults and Compose port publishing exposed services
     beyond localhost.
   - Fix: Changed local defaults to `127.0.0.1` and updated Compose port mappings
     to publish on loopback by default. Container-internal binds can still use
     `0.0.0.0` when Docker needs it.
   - Follow-up: Require an explicit production profile or documented
     `HUEY_BIND_ADDR=0.0.0.0` override for remote access.

4. **noVNC/VNC exposed without a password**
   - Concern: The VNC image started `x11vnc` with `-nopw`, exposing a GUI session
     to anyone who can reach the port.
   - Fix: The VNC startup script now requires `VNC_PASSWORD`, stores it in a
     temporary x11vnc password file, and binds the raw VNC listener to localhost
     inside the container.
   - Follow-up: Put noVNC behind TLS/reverse proxy auth for non-local use.

5. **Shell command execution via `--sys-code`**
   - Concern: `run_sys_code()` used `shell=True`, making shell metacharacter
     injection easier if untrusted input ever reached the option.
   - Fix: It now splits the command and calls `subprocess.run()` without a shell.
   - Follow-up: Consider removing `--sys-code` or gating it behind an explicit
     unsafe/developer mode.

## Remaining concerns

1. **Dependency vulnerability scanning is not enforced locally**
   - Fix: Add `pip-audit` or equivalent to CI and run it against the pinned base
     requirements plus selected extras.

2. **GitHub Actions use major-version tags**
   - Fix: Pin security-critical actions to commit SHAs and let Dependabot update
     them.

3. **Large bundled archives, PDFs, binaries, and vendored packages increase
   review surface**
   - Fix: Move bulky/generated artifacts to releases or object storage, keep
     checksums in Git, and scan binaries before publication.

4. **Submodule follows a moving upstream branch**
   - Fix: Keep the submodule pinned to reviewed commits and avoid automated
     branch tracking in release builds.

5. **Many legacy management helpers perform powerful host/container actions**
   - Fix: Keep them local-only, require operator confirmation for destructive
     actions, and add integration tests around command construction.
