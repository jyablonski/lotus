"""Smoke tests to verify all Dagster definitions can be imported."""

import json
import os
import subprocess
import sys

import pytest

from dagster_project.definitions import all_jobs, all_schedules, defs


@pytest.mark.unit
def test_jobs_are_loadable():
    """Verify definitions exports at least one job without import errors."""
    assert len(all_jobs) > 0, "No jobs registered in definitions"


@pytest.mark.unit
def test_schedules_are_loadable():
    """Verify definitions exports at least one schedule without import errors."""
    assert len(all_schedules) > 0, "No schedules registered in definitions"


@pytest.mark.unit
def test_definitions_object_loads():
    """Verify the definitions object loads without errors."""
    assert defs is not None


@pytest.mark.unit
def test_example_definitions_are_excluded_by_default():
    """Demo/example assets and jobs should not appear in the default code location."""
    job_names = {job.name for job in all_jobs}
    asset_keys = {spec.key.to_user_string() for spec in defs.resolve_all_asset_specs()}

    assert "hello_world_example_job" not in job_names
    assert "sync_users_job" not in job_names
    assert "incremental_example_api_job" not in job_names
    assert "hello_world_asset" not in asset_keys
    assert "get_api_users" not in asset_keys
    assert "users_in_postgres" not in asset_keys
    assert "example_api_records_incremental" not in asset_keys


@pytest.mark.unit
def test_example_definitions_can_be_opted_in():
    env = os.environ.copy()
    env["DAGSTER_INCLUDE_EXAMPLES"] = "true"

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import json; "
                "from dagster_project.definitions import all_jobs, defs; "
                "print(json.dumps({"
                "'jobs': sorted(job.name for job in all_jobs), "
                "'assets': sorted("
                "spec.key.to_user_string() for spec in defs.resolve_all_asset_specs()"
                ")"
                "}))"
            ),
        ],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert "hello_world_example_job" in payload["jobs"]
    assert "sync_users_job" in payload["jobs"]
    assert "incremental_example_api_job" in payload["jobs"]
    assert "hello_world_asset" in payload["assets"]
    assert "get_api_users" in payload["assets"]
    assert "users_in_postgres" in payload["assets"]
    assert "example_api_records_incremental" in payload["assets"]


@pytest.mark.unit
def test_real_jobs_remain_registered():
    job_names = {job.name for job in all_jobs}

    assert {
        "daily_sales_job",
        "get_game_types_job",
        "llm_prompt_from_db_job",
        "llm_prompt_from_sheet_job",
        "sync_flags_to_sheets_job",
        "unload_journal_entries_job",
    }.issubset(job_names)


@pytest.mark.unit
def test_registered_jobs_have_standard_tags():
    required_tags = {"audience", "domain", "pii"}

    for job in all_jobs:
        assert required_tags.issubset(job.tags), f"{job.name} is missing standard tags"
