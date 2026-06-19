from dagster_project.assets.transformations.dbt_assets import (
    dbt_gold_analytics,
    dbt_silver_core,
    dbt_silver_stg,
)
from dagster_project.jobs.utils import Audience, Domain, create_job, dbt_tag_selection

# Only create the job if dbt assets are available
staging_selection = dbt_tag_selection([dbt_silver_stg], tag="staging")
core_selection = dbt_tag_selection([dbt_silver_core], tag="core")
analytics_selection = dbt_tag_selection([dbt_gold_analytics], tag="analytics")

if (
    staging_selection is not None
    and core_selection is not None
    and analytics_selection is not None
):
    # Dagster respects asset dependencies from the dbt manifest,
    # so execution order is staging -> core -> analytics.
    all_dbt_selection = staging_selection | core_selection | analytics_selection

    dbt_pipeline_job = create_job(
        name="dbt_pipeline_job",
        selection=all_dbt_selection,
        audience=Audience.INTERNAL,
        domain=Domain.ANALYTICS,
        pii=True,
        description="Builds dbt models in stages: staging -> core -> analytics",
    )
else:
    dbt_pipeline_job = None
