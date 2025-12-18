"""Tests for Dagster jobs and schedules."""

import pytest
from dagster_project.definitions import all_jobs, all_schedules


# =============================================================================
# Global registry - update these when adding new jobs/schedules
# =============================================================================

EXPECTED_JOBS = [
    "get_game_types_job",
    "daily_sales_job",
    "sync_users_job",
    "hello_world_example_job",
    "unload_journal_entries_job",
]

EXPECTED_SCHEDULES = [
    "sync_users_schedule",
    "daily_sales_schedule",
]


# =============================================================================
# Registry tests
# =============================================================================


@pytest.mark.unit
def test_all_expected_jobs_are_registered():
    """Verify all expected jobs are registered in definitions."""
    registered_job_names = {job.name for job in all_jobs}
    for expected_job in EXPECTED_JOBS:
        assert expected_job in registered_job_names, (
            f"Job '{expected_job}' not found in definitions"
        )


@pytest.mark.unit
def test_no_unexpected_jobs():
    """Verify no unexpected jobs are registered."""
    registered_job_names = {job.name for job in all_jobs}
    for job_name in registered_job_names:
        assert job_name in EXPECTED_JOBS, (
            f"Unexpected job '{job_name}' found - add it to EXPECTED_JOBS"
        )


@pytest.mark.unit
def test_all_expected_schedules_are_registered():
    """Verify all expected schedules are registered in definitions."""
    registered_schedule_names = {schedule.name for schedule in all_schedules}
    for expected_schedule in EXPECTED_SCHEDULES:
        assert expected_schedule in registered_schedule_names, (
            f"Schedule '{expected_schedule}' not found in definitions"
        )


@pytest.mark.unit
def test_no_unexpected_schedules():
    """Verify no unexpected schedules are registered."""
    registered_schedule_names = {schedule.name for schedule in all_schedules}
    for schedule_name in registered_schedule_names:
        assert schedule_name in EXPECTED_SCHEDULES, (
            f"Unexpected schedule '{schedule_name}' found - add it to EXPECTED_SCHEDULES"
        )
