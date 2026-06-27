import pytest

from dagster_project.definitions import _PROJECT_ROOT, all_jobs, all_schedules, defs


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
def test_definitions_loader_uses_project_root():
    assert (_PROJECT_ROOT / "pyproject.toml").is_file()


@pytest.mark.unit
def test_example_definitions_are_registered():
    job_names = {job.name for job in all_jobs}
    asset_keys = {spec.key.to_user_string() for spec in defs.resolve_all_asset_specs()}

    assert "hello_world_example_job" in job_names
    assert "sync_users_job" in job_names
    assert "incremental_example_api_job" in job_names
    assert "hello_world_asset" in asset_keys
    assert "get_api_users" in asset_keys
    assert "users_in_postgres" in asset_keys
    assert "example_api_records_incremental" in asset_keys


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
def test_resources_remain_registered():
    """Explicit resources should be loaded through the defs autoload bridge."""
    assert {
        "api_client",
        "feast_store",
        "feature_flags_google_sheet",
        "llm_prompt_google_sheet",
        "openai_client",
        "postgres_conn",
        "redis_conn",
        "s3_resource",
        "slack_resource",
    }.issubset(defs.resources)


@pytest.mark.unit
def test_registered_jobs_have_standard_tags():
    required_tags = {"audience", "domain", "pii"}

    for job in all_jobs:
        assert required_tags.issubset(job.tags), f"{job.name} is missing standard tags"
