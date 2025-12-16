"""Tests for Dagster jobs."""

import pytest
from dagster_project.jobs.sync_users_job import sync_users_job


@pytest.mark.unit
class TestSyncUsersJob:
    """Test the sync_users_job definition."""

    def test_job_definition(self):
        """Test that the job is properly defined."""
        from dagster_project.definitions import defs

        assert sync_users_job.name == "sync_users_job"
        # Resolve the job to access its selection
        resolved_job = defs.get_job_def("sync_users_job")
        # Access selection via the resolved job's op_selection property
        selection = resolved_job.op_selection
        resolved_assets = selection.resolve(defs.get_all_asset_defs())
        assert len(resolved_assets) == 2
        asset_keys = [asset.key.to_user_string() for asset in resolved_assets]
        assert "api_users" in asset_keys
        assert "users_in_postgres" in asset_keys

    def test_schedule_definition(self):
        """Test that the schedule is properly defined."""
        from dagster_project.jobs.sync_users_job import sync_users_schedule

        assert sync_users_schedule.job == sync_users_job
        assert sync_users_schedule.cron_schedule == "0 12 * * *"
