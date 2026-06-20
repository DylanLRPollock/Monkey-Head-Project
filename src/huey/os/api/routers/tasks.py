"""Task management API routes."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Request, status

from huey.os.core.task_scheduler import ResourceProfile, TaskStatus
from huey.os.services.tasks import (
    TaskListResponse,
    TaskResponse,
    TaskSubmissionRequest,
)

router = APIRouter(tags=["Task Management"])


def _legacy_api_module():
    from huey.memory.PY import api as legacy_api

    return legacy_api


@router.post(
    "/tasks", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED
)
def submit_task(request: TaskSubmissionRequest, http_request: Request) -> TaskResponse:
    """Submit a task for execution by Spark or Zap."""

    legacy_api = _legacy_api_module()
    if legacy_api._requires_scheduler_auth():
        legacy_api.require_strong_api_auth(http_request)
    legacy_api._require_unsafe_task_submission_access(http_request)
    profile = (
        request.resource_profile.to_profile()
        if request.resource_profile is not None
        else ResourceProfile()
    )
    record = legacy_api.SCHEDULER.submit_task(
        command=request.command,
        priority=request.priority,
        requested_agent=request.requested_agent,
        metadata=dict(request.metadata),
        resource_profile=profile,
    )
    return TaskResponse.from_record(record)


@router.get("/tasks", response_model=TaskListResponse)
def list_tasks_endpoint(
    http_request: Request,
    status_filter: Optional[List[TaskStatus]] = Query(
        None,
        alias="status",
        description="Filter results to tasks with the specified status",
    ),
) -> TaskListResponse:
    """List known tasks with optional status filters."""

    legacy_api = _legacy_api_module()
    if legacy_api._requires_scheduler_auth():
        legacy_api.require_strong_api_auth(http_request)
    records = legacy_api.SCHEDULER.list_tasks(status_filter)
    return TaskListResponse(
        tasks=[TaskResponse.from_record(record) for record in records]
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, http_request: Request) -> TaskResponse:
    """Return the scheduler record for a specific task."""

    legacy_api = _legacy_api_module()
    if legacy_api._requires_scheduler_auth():
        legacy_api.require_strong_api_auth(http_request)
    try:
        record = legacy_api.SCHEDULER.get_task(task_id)
    except KeyError as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return TaskResponse.from_record(record)


@router.post(
    "/tasks/{task_id}/cancel",
    response_model=TaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def cancel_task(task_id: str, http_request: Request) -> TaskResponse:
    """Cancel a pending or running task."""

    legacy_api = _legacy_api_module()
    if legacy_api._requires_scheduler_auth():
        legacy_api.require_strong_api_auth(http_request)
    try:
        record = legacy_api.SCHEDULER.cancel_task(task_id)
    except KeyError as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return TaskResponse.from_record(record)
