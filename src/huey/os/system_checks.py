"""Compatibility shim exposing legacy huey.system_checks via huey.os.system_checks."""

from huey.system_checks import *  # noqa: F401,F403
