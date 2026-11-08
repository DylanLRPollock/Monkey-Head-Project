"""Deny-by-default intent policy for privileged host operations.

This local gate is not a substitute for identity verification or RBAC.
Network ingress and agent/plugin integrations must authenticate separately.
"""

from __future__ import annotations

from typing import Literal

Capability = Literal["read-only", "mutating", "destructive"]
OperatorRole = Literal["reader", "operator", "admin"]

OPERATIONS: dict[str, Capability] = {
    "host.shutdown": "destructive",
    "host.reboot": "destructive",
    "host.hibernate": "destructive",
    "host.sleep": "destructive",
    "project.uninstall": "destructive",
    "project.install": "mutating",
    "project.update": "mutating",
    "project.run": "mutating",
}


def authorize_privileged_operation(
    operation: str,
    *,
    confirmed: bool = False,
    actor_role: OperatorRole | None = None,
    dry_run: bool = False,
) -> bool:
    """Return False for dry-run; otherwise require explicit intent and role.

    Unknown operations fail closed. The actor_role argument is a claim from
    the caller, not proof of identity; the calling surface must verify it.
    """
    capability = OPERATIONS.get(operation)
    if capability is None:
        raise PermissionError(f"Unknown privileged operation: {operation}")
    if dry_run:
        return False
    if not confirmed:
        raise PermissionError(f"Explicit confirmation required: {operation}")
    allowed_roles = {"admin"} if capability == "destructive" else {"operator", "admin"}
    if actor_role not in allowed_roles:
        raise PermissionError(f"Operator role not authorized: {operation}")
    return True


__all__ = [
    "OPERATIONS",
    "Capability",
    "OperatorRole",
    "authorize_privileged_operation",
]
