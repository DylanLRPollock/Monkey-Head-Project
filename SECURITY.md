---

# Security Policy

| Field | Value |
|---|---|
| **Project** | Monkey-Head-Project / HueyOS |
| **Policy line** | v201.x candidate |
| **Last updated** | 2026-07-17 |
| **Policy owner** | Dylan L.R. Pollock |

> [!IMPORTANT]
> This policy governs security reporting, triage, remediation, disclosure, release handling, and good-faith research for the repository and its officially documented artifacts. It does not declare planned or partially implemented architecture to be secure, operational, or production-ready.

HueyOS is an offline-first, self-hosted embodied-AI project with software, hardware, messaging, controller, model, and eventual physical-actuation surfaces. Security therefore includes ordinary software security as well as command authenticity, physical safety, device replacement, auditability, recovery, and clear authority boundaries.

Every privileged or externally reachable interface is treated as potentially hostile, including HTTP APIs, local IPC, HIMS messages, PyHuey, HueyNexusController devices, model-loading paths, automation tools, release pipelines, external connectors, and Huey Body commands.

Security claims must preserve the project truth classes: **current reality**, **accepted direction**, **provisional choice**, **unresolved**, **target state**, and **historical lineage**.

---

## 1. Purpose and Scope

This policy covers security reporting, triage, remediation, disclosure, release handling, and good-faith research for the repository and its officially documented artifacts.

It applies to maintained or officially documented project surfaces, including software, hardware, messaging, controllers, models, connectors, deployment artifacts, and physical-control boundaries.

---

## 2. Security Principles

1. **Human authority remains explicit.** Dylan L.R. Pollock remains the present canon authority. Models, agents, controllers, tools, and messages do not independently acquire governance or physical-control authority.
2. **Delivery is not authorization.** A received HIMS or controller command must still pass authentication, authorization, validation, policy, confirmation, and safe-execution checks.
3. **Controllers are replaceable.** Nexus devices and other operator surfaces do not contain Huey’s identity or canonical memory.
4. **Offline-first is not risk-free.** Local, physical, supply-chain, model, and recovery attacks remain relevant.
5. **Least privilege is the default.** Services and devices receive only the permissions needed for their bounded role.
6. **Recovery is part of security.** Revocation, rollback, safe-stop, replacement, backup, and restore procedures are required controls.
7. **Unimplemented safeguards receive no credit.** Plans and diagrams are not substitutes for working controls and evidence.
8. **Private material remains private.** Credentials, private archives, continuity profiles, and sensitive logs must not enter public artifacts by default.

---

## 3. Supported Versions

Monkey-Head-Project uses several version layers:

| Version layer | Examples |
|---|---|
| Repository and master-plan lines | `v120.x`, `v201.x` |
| Package versions | Semantic versioning where appropriate |
| Hardware, image, and controller releases | Release identifiers |
| Website release lines | DLRP.ca `v200.x` |

A version number alone does not establish security support.

| Support class | Security status |
|---|---|
| Current accepted release | Receives security fixes and advisories where feasible |
| Previous designated supported release | Critical and high-severity fixes where feasible |
| Current `main` branch | Fixes normally land here first; may contain unreleased changes |
| Draft PRs and feature branches | Unsupported and potentially incomplete |
| Historical releases and archives | Unsupported unless an advisory explicitly says otherwise |
| External forks | Must define their own support window |

Each supported release should identify its exact commit, platform profile, dependency baseline, known limitations, and supersession condition.

Security fixes normally land on `main` first. Backports are evaluated according to severity, deployment use, testability, compatibility, and regression risk.

---

## 4. Supported Platforms

Security support is granted through documented and validated **platform profiles**, not merely by operating-system or architecture name.

### Primary Compute Environments

Current project direction centers:

- Debian 14 “Forky” on documented `amd64` systems;
- approved project kernel baselines;
- supported Python 3.13 environments;
- documented containers and virtual machines;
- approved LabTech systems used for development, testing, and recovery.

A system is not security-supported simply because HueyOS starts on it.

### Nexus and ARM Controller Targets

ARM is in project scope for HueyNexusController:

- Nexus 5 `hammerhead`;
- Nexus 7 `grouper`;
- Nexus 7 `tilapia`;
- Nexus 7 `flo`;
- Nexus 7 `deb`.

These are supported project targets. A specific image becomes **security-validated** only when its release record documents the boot and recovery path, image checksum, kernel and firmware, hardware support, controller version, device provisioning, secret storage, HIMS protocol, update and rollback path, battery status, and known limitations.

Native Debian remains the primary direction and LineageOS the fallback where needed. Neither environment receives blanket approval across every device variant.

### Containers, Virtual Machines, and Hosts

Official container, VM, compose, and systemd examples are in scope. Operators remain responsible for host patching, network exposure, storage encryption, account policy, physical access, hypervisor security, and backup protection.

---

## 5. Reporting a Vulnerability

Use coordinated private disclosure.

### Preferred Channels

1. **GitHub Private Vulnerability Reporting** — repository **Security** tab → **Report a vulnerability**.
2. **Email** — `admin@dlrp.ca` with subject `VULN: <short title>`.

For active exploitation, credential exposure, unsafe physical control, or a lost controller with active credentials, use `URGENT VULN:` in the subject.

Do not open a public issue, discussion, or pull request containing exploit details, credentials, sensitive logs, or private configuration before a disclosure plan is agreed.

### Include

- summary and impact;
- affected component, version, commit, image, or device;
- deployment mode and reachability;
- reproduction steps or proof of concept;
- commands, requests, payloads, or HIMS message envelopes;
- expected and observed behavior;
- required privileges and prerequisites;
- OS, architecture, kernel, firmware, and dependencies;
- whether PyHuey, HIMS, Huey Body, Nexus controllers, models, or connectors are involved;
- physical-safety implications;
- mitigations or workarounds;
- preferred credit or anonymity.

Redact secrets. Request an encrypted transfer method before sending unredacted sensitive material.

---

## 6. Triage and Severity

CVSS v3.1 may be used as a reference, but practical severity also considers deployment reality.

Relevant factors include default exposure, authentication, attacker privileges, exploit reliability, secret access, controller impersonation, HIMS replay or tampering, Body authorization bypass, safe-stop failure, physical injury risk, persistence, release-pipeline compromise, and recovery impact.

| Severity | Typical examples |
|---|---|
| Critical | Unauthenticated RCE, arbitrary physical actuation, signing-key compromise, remote safe-stop bypass |
| High | Privilege escalation, controller impersonation, HIMS authorization bypass, sensitive key disclosure |
| Medium | Limited data exposure, realistic denial of service, meaningful insecure default |
| Low | Minor information disclosure or narrow hardening weakness |

Best-effort targets:

| Stage | Target |
|---|---|
| Acknowledgement | Within 72 hours |
| Initial triage | Within 7 calendar days |
| Critical mitigation or fix | Within 14–21 days |
| High | Within 21–30 days |
| Medium | Within 30–60 days |
| Low | Based on impact and capacity |

Active exploitation, unsafe movement, or credential compromise may require immediate containment before a complete fix.

---

## 7. Coordinated Disclosure

The default embargo is 90 days from acknowledgement.

It may be shortened for active exploitation, broad default exposure, or an immediately available mitigation. It may be extended by agreement for hardware, firmware, upstream coordination, architectural remediation, or multi-platform validation.

Qualifying issues may receive a GitHub Security Advisory and CVE. Advisories should state affected and fixed versions, prerequisites, impact, mitigations, upgrade or revocation steps, rollback instructions, and known limitations.

---

## 8. Fix, Backport, and Release Policy

When a vulnerability is confirmed:

1. Containment and mitigation are evaluated.
2. Private development is used when disclosure risk requires it.
3. Regression tests are added where feasible.
4. The fix normally lands on `main`.
5. Supported lines are evaluated for backport.
6. Affected artifacts are rebuilt, revoked, or withdrawn.
7. Checksums and manifests are regenerated.
8. Operators receive remediation guidance.

Security releases should include exact commit and artifact identifiers, checksums, file inventories, build provenance, affected and fixed versions, validation performed, upgrade instructions, rollback instructions, required key rotation or device revocation, and unresolved limitations.

A release should fail validation when it includes credentials, private keys, corrupt required files, unexplained binary payloads, stale security configuration, private archive material, inconsistent manifests, or missing checksums.

---

## 9. Credential and Identity Compromise

Immediately report:

- committed API keys, passwords, tokens, or private keys;
- secrets in images, packages, logs, or CI artifacts;
- lost or stolen Nexus controllers with active credentials;
- copied or reused HIMS keys;
- signing-key exposure;
- connector or OAuth credential leakage;
- unredacted secrets in backups.

Response priorities are revocation or rotation, isolation of affected systems, exposure assessment, artifact replacement, operator notification, and forensic preservation without republishing the secret.

History rewriting may reduce accidental exposure but never replaces credential rotation.

Each controller should use device-specific credentials and support revocation, replacement, re-provisioning, and retained audit identity.

---

## 10. HIMS Security

HIMS is messaging and record infrastructure, not automatic execution authority.

Security-sensitive HIMS work must address:

- authenticated sender and recipient identity;
- message integrity;
- replay protection;
- unique identifiers;
- expiry and freshness;
- authorization separate from delivery;
- acknowledgement and duplicate-delivery semantics;
- queue and storage permissions;
- secret-safe logging;
- key rollover and revocation;
- reconnect and offline behavior;
- audit retention and tamper evidence;
- refusal and safe-failure paths.

A successfully delivered message must never be treated as sufficient authorization for physical action.

---

## 11. Huey Body and Physical-Control Security

Physical-control vulnerabilities receive elevated priority.

Body-facing commands should pass through:

1. Authenticated origin.
2. Schema and range validation.
3. Authorization.
4. Current-state and interlock checks.
5. Operator confirmation where required.
6. Rate, motion, and power limits.
7. Supervised execution.
8. Safe-stop and refusal.
9. Attributable logging.

In-scope examples include safe-stop bypass, stale or replayed movement, unsafe simultaneous commands, controller impersonation, loss of operator visibility, thermal or battery-control failures, and denial of service that prevents recovery.

Do not conduct hazardous physical testing without prior coordination and bounded safeguards.

---

## 12. HueyNexusController Security

Nexus controllers are dedicated, replaceable operator hardware outside Huey’s identity boundary.

Security requirements include:

- documented image provenance and checksums;
- recoverable boot and re-image procedure;
- device-specific provisioning;
- protected secret storage appropriate to the device;
- authentication failure and safe-state behavior;
- revocation and replacement workflow;
- controlled update and rollback;
- minimal installed software;
- no personal data in controller images;
- explicit microphone, camera, and sensor permissions;
- logs that exclude credentials and unnecessary audio;
- battery, charging, thermal, and inspection records;
- support matrix by device variant.

A controller may request movement, shutdown, or recovery, but cannot bypass Body authorization or safe-stop logic.

---

## 13. AI, Model, Prompt, and Tool Security

AI-specific risks are in scope when they affect confidentiality, integrity, authority, availability, or physical safety.

Examples include:

- prompt injection causing unauthorized tool use;
- model output treated as trusted code or command input;
- indirect prompt injection through files, webpages, email, or HIMS;
- untrusted model repositories executing code;
- unsafe model deserialization;
- model-registry compromise;
- connector or tool-based data exfiltration;
- cross-session data leakage;
- agents modifying canon, security policy, or physical controls without authorization;
- hidden instructions in imported files overriding project boundaries.

Model output and model metadata must be treated as untrusted input unless a narrower validated contract exists.

### Remote Model Code

Do not rely solely on `trust_remote_code=False` as a universal security boundary. Model-loading code must use patched dependencies, trusted repositories, pinned revisions where practical, isolated execution for untrusted artifacts, and review of custom-code requirements.

The repository must not declare a vulnerable `transformers` release below the patched baseline required by active advisories.

---

## 14. Supply-Chain and Dependency Security

Expectations include:

- dependency constraints or pins;
- prompt review of security alerts;
- provenance for copied and vendored code;
- checksums for downloaded artifacts;
- avoidance of unverified install scripts run as root;
- minimal CI permissions;
- review of GitHub Actions and third-party actions;
- documented model and dataset origins;
- separation of build and runtime credentials;
- rollback and replacement plans.

An upstream vulnerability is project-relevant when HueyOS defaults or integrations make it exploitable.

---

## 15. Logging, Privacy, and Evidence

Security logs should preserve useful evidence while minimizing secrets and personal data.

Recommended fields include transaction identifier, UTC timestamps, authenticated device identity, message or command identifier, authorization decision, stage transitions, software version, hardware profile, errors, recovery actions, and final status.

Do not write passwords, tokens, private keys, authentication headers, raw secret-bearing configuration, private continuity profiles, unnecessary personal data, or unapproved audio/video into ordinary logs.

Security-sensitive records should have defined ownership, access controls, retention, deletion, backup, and disclosure classification.

---

## 16. Scope

In scope when maintained or officially documented by this repository:

- HueyOS runtime and packages;
- PyHuey;
- HIMS;
- CLI tools and scripts;
- configuration and systemd units;
- installers and image builders;
- containers and deployment manifests;
- official model, prompt, plugin, and connector integrations;
- release, update, signing, and packaging processes;
- HueyNexusController images and documentation;
- Huey Body command and safety boundaries;
- LabTech recovery paths;
- documented default settings;
- official project artifacts.

Generally out of scope unless they create a practical project-specific risk:

- pure upstream defects with no HueyOS exposure;
- unrelated social engineering;
- unrealistic denial of service;
- intentionally public information;
- unsupported historical branches or private forks;
- arbitrary configuration that directly contradicts documentation;
- cosmetic findings with no security or safety impact.

Physical-access findings remain in scope when secrets cannot be revoked, controllers can be cloned, later remote compromise becomes possible, a documented security boundary fails, or a feasible mitigation exists.

---

## 17. Safe Harbor

We support good-faith security research and will not initiate legal action solely for research on this project when the researcher:

- acts lawfully;
- respects privacy and data ownership;
- avoids unnecessary access, modification, or exfiltration;
- does not endanger people, animals, property, batteries, or hardware;
- avoids large-scale denial of service;
- reports privately;
- allows reasonable remediation time;
- deletes sensitive data when no longer needed;
- does not use extortion or payment demands to withhold exploitation.

This does not authorize testing against systems, accounts, devices, or data without permission. Contact us first when testing may involve physical movement, electrical or battery risk, live credentials, private data, or shared infrastructure.

---

## 18. Prioritized Vulnerability Classes

We especially prioritize:

- remote code execution and injection;
- privilege escalation and sandbox escape;
- authentication and authorization bypass;
- HIMS spoofing, replay, tampering, and routing flaws;
- controller impersonation and failed revocation;
- unsafe Body actuation or safe-stop bypass;
- filesystem, temp-file, and path-traversal attacks;
- secret, key, prompt, model, log, or backup disclosure;
- model, plugin, tool, and prompt-injection vulnerabilities;
- insecure update, signing, and release pipelines;
- supply-chain compromise;
- insecure defaults and network exposure;
- battery, thermal, charging, and power failures with safety impact;
- denial of service that blocks recovery;
- boundary confusion between Huey, Atlas, LabTech, controllers, Farm, and external services.

---

## 19. Development and Hardening Expectations

Security-sensitive changes should include, where practical:

- threat or abuse-case notes;
- explicit trust and authority boundaries;
- least-privilege identities;
- schema and input validation;
- secret-safe configuration;
- timeout, retry, replay, and duplicate handling;
- failure-path and regression tests;
- safe-stop and recovery behavior;
- dependency and artifact provenance;
- operator-visible status;
- documented unsupported states;
- rollback, rotation, or revocation procedure.

A security-relevant PR should explain what changed, affected surfaces, threat addressed, assumptions, validation, limitations, and required operator action.

---

## 20. Incident Response

A security incident includes confirmed exploitation, credential exposure, malicious artifacts, controller loss, unauthorized physical action, or compromise of a trusted build or deployment system.

Response phases:

1. **Contain** — disable services, revoke devices or credentials, isolate systems, and stop unsafe movement.
2. **Preserve evidence** — retain relevant logs, commits, images, timestamps, and configuration without spreading secrets.
3. **Assess** — determine scope, persistence, affected users, hardware, and artifacts.
4. **Eradicate** — patch, rebuild, rotate, re-image, or replace affected components.
5. **Recover** — restore from known-good sources and verify normal operation.
6. **Communicate** — publish advisories and operator instructions where required.
7. **Learn** — add tests, controls, and documentation.

For suspected unsafe Body behavior, prioritize physical stop and power isolation. Do not rely solely on the software path that may be compromised.

---

## 21. Report Template

```text
Subject: VULN: <short title> - impact <Critical/High/Medium/Low>

Product: Monkey-Head-Project / HueyOS
Affected versions, commits, images, or devices:
Environment: OS / architecture / kernel / firmware / dependencies
Reachability: local / LAN / internet / physical / controller / HIMS

Summary:
<Concise description and impact>

Reproduction:
<Steps, requests, commands, payloads, or message envelopes>

Privileges and prerequisites:
<Required access, configuration, or hardware>

Impact:
<What an attacker can read, change, impersonate, interrupt, or physically control>

Evidence:
<Logs, screenshots, checksums, or traces with secrets removed>

Suggested mitigation:
<Optional>

Reporter credit:
<Name, handle, link, or anonymity request>
```

---

## 22. Policy Maintenance

Review this policy when the accepted architecture, supported release line, HIMS authority model, Body actuation path, Nexus support matrix, update mechanism, public network exposure, OS/kernel/Python baseline, governance authority, or private reporting channel changes.

Historical versions remain available through Git history. Current claims must be supported by current implementation, release, and repository evidence.