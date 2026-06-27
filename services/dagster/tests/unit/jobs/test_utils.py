import pytest
from dagster import AssetSelection, asset

from dagster_project.defs.jobs.utils import (
    Audience,
    Domain,
    create_job,
    schedule_for_job,
    standard_tags,
)


@asset
def first_asset():
    return None


@asset
def second_asset():
    return None


@pytest.mark.unit
def test_create_job_returns_only_job_when_schedule_is_omitted():
    job = create_job(
        name="example_manual_job",
        assets=[first_asset],
        audience=Audience.INTERNAL,
        domain=Domain.OPS,
        pii=False,
    )

    assert job.name == "example_manual_job"
    assert job.tags == {"audience": "internal", "domain": "ops", "pii": "false"}


@pytest.mark.unit
def test_create_job_returns_job_and_schedule_when_schedule_is_provided():
    job, schedule = create_job(
        name="example_scheduled_job",
        assets=[first_asset, second_asset],
        audience=Audience.INTERNAL,
        domain=Domain.OPS,
        pii=False,
        schedule="15 6 * * *",
        execution_timezone="America/Los_Angeles",
        description="Example scheduled asset job",
    )

    assert job.name == "example_scheduled_job"
    assert job.tags == {"audience": "internal", "domain": "ops", "pii": "false"}
    assert job.description == "Example scheduled asset job"
    assert schedule.name == "example_scheduled_job_schedule"
    assert schedule.job_name == "example_scheduled_job"
    assert schedule.cron_schedule == "15 6 * * *"
    assert schedule.execution_timezone == "America/Los_Angeles"


@pytest.mark.unit
def test_create_job_allows_explicit_schedule_name_override():
    _job, schedule = create_job(
        name="example_scheduled_job",
        assets=[first_asset],
        audience=Audience.INTERNAL,
        domain=Domain.OPS,
        pii=False,
        schedule="15 6 * * *",
        schedule_name="example_daily_schedule",
    )

    assert schedule.name == "example_daily_schedule"


@pytest.mark.unit
def test_schedule_for_job_defaults_name_from_job_name():
    job = create_job(
        name="example_manual_job",
        assets=[first_asset],
        audience=Audience.INTERNAL,
        domain=Domain.OPS,
        pii=False,
    )
    schedule = schedule_for_job(job=job, cron_schedule="15 6 * * *")

    assert schedule.name == "example_manual_job_schedule"


@pytest.mark.unit
def test_create_job_accepts_prebuilt_selection_for_custom_jobs():
    job = create_job(
        name="example_selection_job",
        selection=AssetSelection.assets(first_asset, second_asset),
        audience=Audience.INTERNAL,
        domain=Domain.OPS,
        pii=False,
    )

    assert job.name == "example_selection_job"


@pytest.mark.unit
def test_create_job_requires_one_selection_style():
    with pytest.raises(ValueError, match="Pass exactly one of assets or selection"):
        create_job(
            name="missing_selection_job",
            audience=Audience.INTERNAL,
            domain=Domain.OPS,
            pii=False,
        )

    with pytest.raises(ValueError, match="Pass exactly one of assets or selection"):
        create_job(
            name="duplicate_selection_job",
            assets=[first_asset],
            selection=AssetSelection.assets(second_asset),
            audience=Audience.INTERNAL,
            domain=Domain.OPS,
            pii=False,
        )


@pytest.mark.unit
def test_standard_tags_reject_unknown_taxonomy_values():
    with pytest.raises(ValueError):
        standard_tags(audience="external", domain=Domain.OPS, pii=False)

    with pytest.raises(ValueError):
        standard_tags(audience=Audience.INTERNAL, domain="finance", pii=False)
