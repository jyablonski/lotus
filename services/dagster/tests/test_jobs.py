"""Tests for Dagster jobs and schedules."""

import pytest
from dagster_project.definitions import all_assets, all_jobs, all_schedules


# =============================================================================
# Global registry - update these when adding new jobs/schedules
# =============================================================================

EXPECTED_JOBS = {
    "daily_sales_job": {
        "assets": ["sales_data", "sales_summary"],
    },
    "sync_users_job": {
        "assets": ["api_users", "users_in_postgres"],
    },
    "hello_world_job": {
        "assets": ["hello_world_asset"],
    },
}

EXPECTED_SCHEDULES = {
    "sync_users_schedule": {
        "job": "sync_users_job",
        "cron": "0 12 * * *",
    },
    "daily_sales_schedule": {
        "job": "daily_sales_job",
        "cron": "0 1,13 * * *",
    },
}


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


# =============================================================================
# Parameterized job tests
# =============================================================================


@pytest.mark.unit
@pytest.mark.parametrize("job_name,expected", EXPECTED_JOBS.items())
def test_job_definition(job_name, expected):
    """Test that each job is properly defined with correct assets."""
    job = next((j for j in all_jobs if j.name == job_name), None)
    assert job is not None, f"Job '{job_name}' not found"

    resolved_assets = job.selection.resolve(all_assets)
    asset_keys = {asset.to_user_string() for asset in resolved_assets}

    for expected_asset in expected["assets"]:
        assert expected_asset in asset_keys, (
            f"Asset '{expected_asset}' not found in job '{job_name}'"
        )


@pytest.mark.unit
@pytest.mark.parametrize("schedule_name,expected", EXPECTED_SCHEDULES.items())
def test_schedule_definition(schedule_name, expected):
    """Test that each schedule is properly defined."""
    schedule = next((s for s in all_schedules if s.name == schedule_name), None)
    assert schedule is not None, f"Schedule '{schedule_name}' not found"

    assert schedule.job.name == expected["job"], (
        f"Schedule '{schedule_name}' has wrong job"
    )
    assert schedule.cron_schedule == expected["cron"], (
        f"Schedule '{schedule_name}' has wrong cron"
    )
