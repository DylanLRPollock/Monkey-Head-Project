"""Behavioral coverage for the persisted Banana Brain job model."""

import pytest

from huey.banana_brain.job_models import (
    Job,
    JobResult,
    JobState,
    JobTransitionError,
    JobValidationError,
    Priority,
    new_job_id,
)


def test_job_normalizes_defaults_and_identity():
    job = Job(adapter="ollama", payload={}, id="", priority=None)
    assert job.id
    assert job.priority == int(Priority.BACKGROUND)
    assert job.is_active and not job.is_terminal
    assert len({job, Job(adapter="comfyui", payload={}, id=job.id)}) == 1
    assert "Job(id=" in repr(job)
    assert new_job_id() != new_job_id()


def test_state_transitions_and_retry_reset():
    job = Job(adapter="ollama", payload={}, max_attempts=3)
    assert job.can_transition_to("running")
    job.transition_to("running")
    job.transition_to(JobState.FAILED)
    job.attempts = 1
    job.last_error = "retry me"
    job.started_at = job.finished_at = 12.0
    assert job.can_retry
    assert job.reset_for_retry()
    assert job.state is JobState.PENDING
    assert job.started_at is job.finished_at is job.last_error is None
    job.transition_to(JobState.RUNNING)
    job.transition_to(JobState.COMPLETED)
    assert job.is_terminal
    assert not job.reset_for_retry()
    with pytest.raises(JobTransitionError):
        job.transition_to(JobState.PENDING)


def test_time_helpers_cover_missing_and_elapsed_values():
    job = Job(adapter="audio", payload={})
    assert job.age_seconds(now=20) is None
    assert job.remaining_seconds(now=20) is None
    assert not job.is_overdue(now=20)
    job.submitted_at = 10
    job.deadline = 15
    assert job.age_seconds(now=20) == 10
    assert job.remaining_seconds(now=20) == -5
    assert job.is_overdue(now=20)


def test_validation_reports_invalid_fields():
    job = Job(adapter="ollama", payload={})
    job.estimated_vram_bytes = 0
    job.deadline = -1
    job.attempts = -1
    job.max_attempts = 0
    job.owner = 1
    job.idempotency_key = 2
    job.tags = {"ok": 1}
    with pytest.raises(JobValidationError) as error:
        job.validate()
    for field in (
        "estimated_vram_bytes",
        "deadline",
        "attempts",
        "max_attempts",
        "owner",
        "idempotency_key",
        "tags",
    ):
        assert field in str(error.value)


def test_result_and_job_round_trip_tagged_result():
    result = JobResult(ok=True, data={"tokens": 3}, message="done", metrics={"rate": 1})
    restored = Job.from_dict(Job(adapter="ollama", payload={}, result=result).to_dict())
    assert restored.result == result
    assert JobResult.from_dict({"ok": 0, "metrics": {"n": 2, "bad": "x"}}).metrics == {
        "n": 2.0
    }


def test_from_dict_tolerates_legacy_bad_scalars_and_extra_fields():
    job = Job.from_dict(
        {
            "adapter": "audio",
            "payload": None,
            "priority": "bad",
            "deadline": "bad",
            "estimated_vram_bytes": 0,
            "attempts": "bad",
            "max_attempts": 0,
            "extra": "ignored",
            "owner": 7,
        }
    )
    assert job.payload == {}
    assert job.priority == int(Priority.BACKGROUND)
    assert job.deadline is None and job.estimated_vram_bytes is None
    assert job.attempts == 0 and job.max_attempts == 1
    assert job.owner == "7"
    with pytest.raises(JobValidationError, match="missing required field"):
        Job.from_dict({})
    with pytest.raises(JobValidationError, match="invalid job state"):
        Job.from_dict({"adapter": "audio", "state": "unknown"})


def test_malformed_embedded_job_result_is_left_as_data():
    encoded = {"__bb_class__": "JobResult", "metrics": ["not-a-mapping"]}
    assert Job.from_dict({"adapter": "audio", "result": encoded}).result == encoded
