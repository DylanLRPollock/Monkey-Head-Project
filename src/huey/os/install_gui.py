"""Installer helpers for GUI flows."""


def validate_license_acceptance(accepted: bool) -> None:
    if not accepted:
        raise PermissionError("License agreement must be accepted before continuing.")


__all__ = ["validate_license_acceptance"]
