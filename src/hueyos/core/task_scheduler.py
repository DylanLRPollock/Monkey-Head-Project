"""Compatibility shim exposing legacy huey.core.task_scheduler via hueyos.core.task_scheduler."""
from huey.core.task_scheduler import *  # noqa: F401,F403
