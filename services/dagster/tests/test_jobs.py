"""Tests for Dagster jobs."""

import pytest
from dagster_project.jobs.sync_users_job import sync_users_job


@pytest.mark.unit
class TestSyncUsersJob:
    """Test the sync_users_job definition."""

    def test_job_definition(self):
        """Test that the job is properly defined."""
        assert sync_users_job.name == "sync_users_job"
        assert len(sync_users_job.asset_selection) == 2
        assert "api_users" in [
            asset.key.to_user_string()
            for asset in sync_users_job.asset_selection.resolve([])
        ]
        assert "users_in_postgres" in [
            asset.key.to_user_string()
            for asset in sync_users_job.asset_selection.resolve([])
        ]

    def test_schedule_definition(self):
        """Test that the schedule is properly defined."""
        from dagster_project.jobs.sync_users_job import sync_users_schedule

        assert sync_users_schedule.job == sync_users_job
        assert sync_users_schedule.cron_schedule == "0 12 * * *"
