# Manual Secret Rotation Checklist

This checklist documents **manual** secret-rotation actions for security incidents and hygiene events.

## When to rotate

Rotate secrets immediately when any of the following occurs:

- Any historically committed private key.
- Any token pasted into configuration files.
- Any shared development password.
- Any key printed in logs.

## What to rotate

Scope rotation to all affected credential types, including:

- SSH keys.
- API keys.
- Database passwords.
- VNC passwords.
- GitHub tokens.

## Rotation steps

Follow this sequence for each affected secret:

1. Revoke the old secret.
2. Generate a new secret outside the repository.
3. Update local `.env` files or the approved secret manager.
4. Verify the application starts successfully.
5. Confirm the old credential no longer works.

## Git history note

- History rewriting is a separate, deliberate operation.
- Do **not** rewrite history casually as part of this task.
