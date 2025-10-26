# OpenAI API Key Exposure Response

When an OpenAI API key (`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`) is inadvertently exposed, use the following response checklist to contain the leak and prevent reuse.

## 1. Rotate and Reissue the Key
- If production workloads still rely on the credential, create a replacement key in the OpenAI dashboard before revoking the compromised one.
- Update every deployment, CI secret store, and configuration file that references the key so operations continue without interruption.

## 2. Revoke the Leaked Credential
- Sign in to the OpenAI dashboard and revoke the exposed key immediately.
- Capture the revocation timestamp in the incident ticket for auditing.

## 3. Review Access Logs
- Inspect OpenAI usage logs and internal security telemetry for anomalous requests starting from the earliest suspected exposure date.
- Investigate spikes in traffic volume, unexpected models, or access from unfamiliar IP ranges.

## 4. Hardening Follow-Up
- Purge the leaked credential from version control, ticket attachments, build artifacts, and chat transcripts.
- Store the newly issued key in the organization-approved secrets manager with least-privilege access policies.
- Enable or tighten automated secret scanning in CI/CD to prevent future regressions.

## 5. Close Out the Incident
- Document completion of the rotation, revocation, and log review steps in the incident record.
- Close security alerts as "revoked" only after all remediation tasks are complete.

Maintaining a codified runbook ensures that future credential exposures are handled quickly and consistently.
