from dagster import define_asset_job
from dagster_dbt import build_dbt_asset_selection

from dagster_project.assets.transformations.dbt_assets import dbt_analytics

# Only create the job if dbt_analytics is available
if dbt_analytics is not None:
    # Build staging models first (tagged with 'staging')
    staging_selection = build_dbt_asset_selection([dbt_analytics], dbt_select="tag:staging")

    # Build core models (depends on staging, tagged with 'core')
    core_selection = build_dbt_asset_selection([dbt_analytics], dbt_select="tag:core")

    # Build analytics models (depends on core, tagged with 'analytics')
    analytics_selection = build_dbt_asset_selection([dbt_analytics], dbt_select="tag:analytics")

    # Combine all selections - Dagster will respect dependencies and run in order
    # staging -> core -> analytics
    all_dbt_selection = staging_selection | core_selection | analytics_selection

    dbt_pipeline_job = define_asset_job(
        name="dbt_pipeline_job",
        selection=all_dbt_selection,
        description="Builds dbt models in stages: staging -> core -> analytics",
    )
else:
    dbt_pipeline_job = None
