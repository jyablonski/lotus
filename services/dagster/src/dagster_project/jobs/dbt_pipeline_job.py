from dagster import define_asset_job
from dagster_dbt import build_dbt_asset_selection

from dagster_project.assets.transformations.dbt_assets import (
    dbt_gold_analytics,
    dbt_silver_core,
    dbt_silver_stg,
)

# Only create the job if dbt assets are available
if (
    dbt_silver_stg is not None
    and dbt_silver_core is not None
    and dbt_gold_analytics is not None
):
    staging_selection = build_dbt_asset_selection(
        [dbt_silver_stg], dbt_select="tag:staging"
    )
    core_selection = build_dbt_asset_selection([dbt_silver_core], dbt_select="tag:core")
    analytics_selection = build_dbt_asset_selection(
        [dbt_gold_analytics], dbt_select="tag:analytics"
    )

    # Dagster respects asset dependencies from the dbt manifest,
    # so execution order is staging -> core -> analytics.
    all_dbt_selection = staging_selection | core_selection | analytics_selection

    dbt_pipeline_job = define_asset_job(
        name="dbt_pipeline_job",
        selection=all_dbt_selection,
        tags={"audience": "internal", "domain": "analytics", "pii": "true"},
        description="Builds dbt models in stages: staging -> core -> analytics",
    )
else:
    dbt_pipeline_job = None
