# Docker Image Pinning & Update Policy

This repository uses Docker images in both development and runtime workflows. To reduce supply-chain risk and avoid surprise breakage, follow these rules:

## 1) No `:latest` in committed Compose files

- Do not commit Compose services that reference floating `:latest` tags.
- Use explicit versioned tags (for example `redis:7.2-alpine`) or internal build tags (for example `monkey-head-project:0.1.0-dev`).

## 2) Base image upgrades must be reviewed

- Treat base image tag changes as code changes that require pull-request review.
- When updating a base image, document:
  - old tag -> new tag,
  - motivation (security fix, compatibility, feature),
  - any expected runtime impact.

## 3) Digest pinning for production/release images

- Production/release images should be pinned by digest in release manifests, e.g. `image: repo/name:tag@sha256:<digest>`.
- Development Compose stacks may use explicit tags without digests to preserve local workflow flexibility.

## 4) Scheduled rebuild expectations

- Rebuild development images at least monthly to pick up OS/package security updates.
- Rebuild production/release images on a fixed cadence (at least monthly) and immediately for critical CVEs.
- Even with unchanged application code, produce refreshed images to capture upstream security patches.

## 5) Debian release track defaults in this repo

- `bookworm` defaults are treated as stable/runtime-oriented.
- `forky` defaults are treated as **development/testing track** and are intentionally mutable over time.
- Any Dockerfile using `ARG DEBIAN_RELEASE=forky` or `ARG DEBIAN_VERSION=forky` must include a comment noting this is an intentional dev/testing default.
