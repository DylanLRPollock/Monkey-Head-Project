"""Auth and access-control helpers for the API split scaffolding.

For v101.1 stabilization these functions are re-exported from the legacy API
module so behavior remains unchanged while endpoint logic is still centralized.
"""

from __future__ import annotations

from huey.memory.PY import api as _legacy_api

_configured_api_token = _legacy_api._configured_api_token
_is_local_request = _legacy_api._is_local_request
_require_privileged_surface_access = _legacy_api._require_privileged_surface_access
_require_unsafe_task_submission_access = _legacy_api._require_unsafe_task_submission_access
_unsafe_task_submission_enabled = _legacy_api._unsafe_task_submission_enabled

__all__ = [
    "_configured_api_token",
    "_is_local_request",
    "_require_privileged_surface_access",
    "_require_unsafe_task_submission_access",
    "_unsafe_task_submission_enabled",
]
