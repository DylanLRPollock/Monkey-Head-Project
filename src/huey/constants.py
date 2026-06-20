"""System-wide constants for the emerging HueyOS runtime."""

from __future__ import annotations

APP_NAME = "HueyOS"
APP_SLUG = "hueyos"
API_VERSION = "2026.06"
DEFAULT_ENVIRONMENT = "development"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 4488
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_BOOT_PROFILE = "standard"
DEFAULT_PROTOCOL = "hueybus"
DEFAULT_POLICY = "cloud-pyramid"
DEFAULT_STORAGE_ROOT = "memory"
DEFAULT_MEMORY_CAPACITY = 1024
DEFAULT_AGENT_NAMES = ("Spark-4", "Volt-4", "Zap-4", "Watt-4")
DEFAULT_DASHBOARD_SECTIONS = (
    "kernel",
    "agents",
    "storage",
    "governance",
    "hardware",
    "network",
)

__all__ = [
    "APP_NAME",
    "APP_SLUG",
    "API_VERSION",
    "DEFAULT_AGENT_NAMES",
    "DEFAULT_BOOT_PROFILE",
    "DEFAULT_DASHBOARD_SECTIONS",
    "DEFAULT_ENVIRONMENT",
    "DEFAULT_HOST",
    "DEFAULT_LOG_LEVEL",
    "DEFAULT_MEMORY_CAPACITY",
    "DEFAULT_POLICY",
    "DEFAULT_PORT",
    "DEFAULT_PROTOCOL",
    "DEFAULT_STORAGE_ROOT",
]
