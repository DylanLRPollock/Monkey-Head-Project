# Local Secrets

This directory is for local-only development and deployment secrets.

Do not commit generated private keys, API tokens, certificates, or production
configuration. Keep real secret files ignored by Git and inject them through
environment variables, Docker secrets, your deployment platform, or a local
secret manager.

The tracked `huey-key-example` file is a non-secret placeholder only.
