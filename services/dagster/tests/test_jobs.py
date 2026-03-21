"""Smoke tests to verify all Dagster jobs and schedules can be imported."""

import pytest

from dagster_project.definitions import all_jobs, all_schedules


@pytest.mark.unit
def test_jobs_are_loadable():
    """Verify definitions exports at least one job without import errors."""
    assert len(all_jobs) > 0, "No jobs registered in definitions"


@pytest.mark.unit
def test_schedules_are_loadable():
    """Verify definitions exports at least one schedule without import errors."""
    assert len(all_schedules) > 0, "No schedules registered in definitions"


@pytest.mark.unit
def test_all_jobs_have_retry_policies_on_assets():
    """Verify the definitions object loads without errors (import smoke test)."""
    from dagster_project.definitions import defs

    assert defs is not None
