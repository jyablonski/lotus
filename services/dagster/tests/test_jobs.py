"""Tests for Dagster jobs."""

import pytest
from dagster_project.definitions import defs
from dagster_project.jobs.sync_users_job import sync_users_job, sync_users_schedule


@pytest.mark.unit
class TestSyncUsersJob:
    """Test the sync_users_job definition."""

    def test_job_definition(self):
        """Test that the job is properly defined."""
        assert sync_users_job.name == "sync_users_job"
        # For asset jobs, access the selection from the unresolved job definition
        # The selection is available before resolution
        selection = sync_users_job.selection
        # Get all asset definitions from the repository
        repo_def = defs.get_repository_def()
        all_asset_defs = repo_def.get_all_asset_defs()
        resolved_assets = selection.resolve(all_asset_defs)
        assert len(resolved_assets) == 2
        asset_keys = [asset.key.to_user_string() for asset in resolved_assets]
        assert "api_users" in asset_keys
        assert "users_in_postgres" in asset_keys

    def test_schedule_definition(self):
        """Test that the schedule is properly defined."""
        assert sync_users_schedule.job == sync_users_job
        assert sync_users_schedule.cron_schedule == "0 12 * * *"
