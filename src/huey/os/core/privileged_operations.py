"""Deny-by-default intent policy for privileged host operations.

This local gate is not a substitute for identity verification or RBAC.
Network ingress and agent/plugin integrations must authenticate separately.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Literal

Capability = Literal["read-only", "mutating", "destructive"]
OperatorRole = Literal["reader", "operator", "admin"]

LOGGER = logging.getLogger(__name__)

OPERATIONS: dict[str, Capability] = {
    "host.shutdown": "destructive",
    "host.reboot": "destructive",
    "host.hibernate": "destructive",
    "host.sleep": "destructive",
    "project.uninstall": "destructive",
    "project.install": "mutating",
    "project.update": "mutating",
    "project.run": "mutating",
    "project.container.build": "mutating",
    "project.container.start": "mutating",
    "project.container.volumes": "read-only",
    "project.container.networks": "read-only",
    "project.function.read": "read-only",
    "project.kubernetes.deploy": "mutating",
    "project.kubernetes.scale": "mutating",
    "project.container.stop": "destructive",
    "project.container.cleanup": "destructive",
    "project.kubernetes.cleanup": "destructive",
    "project.memory.auto_sort": "mutating",
    "host.package_update": "destructive",
    "host.user_create": "destructive",
    "host.execute_command": "destructive",
    "host.failover_sync": "destructive",
}


def _audit_attempt(
    operation: str,
    capability: Capability | None,
    actor_role: object,
    *,
    confirmed: bool,
    dry_run: bool,
    outcome: Literal["allowed", "denied", "dry_run"],
    reason: str,
) -> None:
    """Write a secret-free structured record for every gate decision."""
    role_claim = (
        actor_role
        if isinstance(actor_role, str) and actor_role in ("reader", "operator", "admin")
        else "unrecognized"
    )
    record = {
        "event": "privileged_operation",
        "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        "operation": operation,
        "capability": capability,
        "role_claim": role_claim,
        "confirmed": confirmed,
        "dry_run": dry_run,
        "outcome": outcome,
        "reason": reason,
    }
    level = logging.WARNING if outcome == "denied" else logging.INFO
    LOGGER.log(level, "%s", json.dumps(record, sort_keys=True, separators=(",", ":")))


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
    audit_operation = operation if capability is not None else "unregistered"
    if capability is None:
        _audit_attempt(
            audit_operation,
            None,
            actor_role,
            confirmed=confirmed is True,
            dry_run=dry_run is True,
            outcome="denied",
            reason="unknown_operation",
        )
        raise PermissionError(f"Unknown privileged operation: {operation}")

    if not isinstance(confirmed, bool) or not isinstance(dry_run, bool):
        _audit_attempt(
            audit_operation,
            capability,
            actor_role,
            confirmed=confirmed is True,
            dry_run=dry_run is True,
            outcome="denied",
            reason="invalid_confirmation_flags",
        )
        raise PermissionError(f"Invalid authorization flags: {operation}")

    if dry_run:
        _audit_attempt(
            audit_operation,
            capability,
            actor_role,
            confirmed=confirmed,
            dry_run=True,
            outcome="dry_run",
            reason="preview_only",
        )
        return False

    if capability == "read-only":
        if not isinstance(actor_role, str) or actor_role not in (
            "reader",
            "operator",
            "admin",
        ):
            _audit_attempt(
                audit_operation,
                capability,
                actor_role,
                confirmed=confirmed,
                dry_run=False,
                outcome="denied",
                reason="role_not_authorized",
            )
            raise PermissionError(f"Operator role not authorized: {operation}")
        _audit_attempt(
            audit_operation,
            capability,
            actor_role,
            confirmed=confirmed,
            dry_run=False,
            outcome="allowed",
            reason="read_only_role",
        )
        return True

    if confirmed is not True:
        _audit_attempt(
            audit_operation,
            capability,
            actor_role,
            confirmed=confirmed,
            dry_run=False,
            outcome="denied",
            reason="confirmation_required",
        )
        raise PermissionError(f"Explicit confirmation required: {operation}")

    allowed_roles = ("admin",) if capability == "destructive" else ("operator", "admin")
    if not isinstance(actor_role, str) or actor_role not in allowed_roles:
        _audit_attempt(
            audit_operation,
            capability,
            actor_role,
            confirmed=confirmed,
            dry_run=False,
            outcome="denied",
            reason="role_not_authorized",
        )
        raise PermissionError(f"Operator role not authorized: {operation}")

    _audit_attempt(
        audit_operation,
        capability,
        actor_role,
        confirmed=confirmed,
        dry_run=False,
        outcome="allowed",
        reason="capability_policy",
    )
    return True


__all__ = [
    "OPERATIONS",
    "Capability",
    "OperatorRole",
    "authorize_privileged_operation",
]
