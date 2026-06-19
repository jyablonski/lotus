from collections.abc import Iterable
from enum import StrEnum
from typing import Any

from dagster import AssetSelection, ScheduleDefinition, define_asset_job
from dagster_dbt import build_dbt_asset_selection


class Audience(StrEnum):
    """Allowed job audience tag values."""

    INTERNAL = "internal"
    USER_FACING = "user-facing"


class Domain(StrEnum):
    """Allowed job domain tag values."""

    ANALYTICS = "analytics"
    FEATURE_STORE = "feature-store"
    GAME = "game"
    INGESTION = "ingestion"
    OPS = "ops"


def standard_tags(*, audience: Audience, domain: Domain, pii: bool) -> dict[str, str]:
    """Build the standard tag set expected on every registered Dagster job."""
    return {
        "audience": Audience(audience).value,
        "domain": Domain(domain).value,
        "pii": str(pii).lower(),
    }


def schedule_for_job(
    *,
    job,
    cron_schedule: str,
    name: str | None = None,
    execution_timezone: str | None = None,
) -> ScheduleDefinition:
    """Create a schedule for a job with optional explicit name and timezone."""
    return ScheduleDefinition(
        name=name or f"{job.name}_schedule",
        job=job,
        cron_schedule=cron_schedule,
        execution_timezone=execution_timezone,
    )


def create_job(
    *,
    name: str,
    audience: Audience,
    domain: Domain,
    pii: bool,
    assets: Iterable[Any] | None = None,
    selection: AssetSelection | None = None,
    schedule: str | None = None,
    schedule_name: str | None = None,
    execution_timezone: str | None = None,
    description: str | None = None,
    hooks: Any = None,
):
    """Create a standard asset job, optionally paired with a cron schedule.

    Pass either ``assets`` for direct asset definitions/keys or ``selection`` for
    a prebuilt Dagster selection such as a dbt tag selection.
    Returns the job when ``schedule`` is omitted. Returns ``(job, schedule_def)``
    when ``schedule`` is provided.
    """
    if (assets is None) == (selection is None):
        raise ValueError("Pass exactly one of assets or selection")

    job_selection = (
        selection if selection is not None else AssetSelection.assets(*assets)
    )

    job = define_asset_job(
        name=name,
        selection=job_selection,
        tags=standard_tags(audience=audience, domain=domain, pii=pii),
        description=description,
        hooks=hooks,
    )

    if schedule is None:
        return job

    return job, schedule_for_job(
        name=schedule_name,
        job=job,
        cron_schedule=schedule,
        execution_timezone=execution_timezone,
    )


def dbt_tag_selection(asset_defs: Iterable[Any], *, tag: str):
    """Build a combined dbt asset selection for one tag across dbt asset defs."""
    selection = None
    for asset_def in asset_defs:
        if asset_def is None:
            return None

        current_selection = build_dbt_asset_selection(
            [asset_def],
            dbt_select=f"tag:{tag}",
        )
        selection = (
            current_selection if selection is None else selection | current_selection
        )

    return selection
