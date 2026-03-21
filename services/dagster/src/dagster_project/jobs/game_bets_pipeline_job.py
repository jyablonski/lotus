from dagster import ScheduleDefinition, define_asset_job
from dagster_dbt import build_dbt_asset_selection

from dagster_project.assets.transformations.dbt_assets import (
    dbt_gold_analytics,
    dbt_silver_core,
    dbt_silver_stg,
)

if dbt_silver_stg is not None:
    staging_selection = build_dbt_asset_selection(
        [dbt_silver_stg],
        dbt_select="tag:game",
    )

    core_selection = build_dbt_asset_selection(
        [dbt_silver_core],
        dbt_select="tag:game",
    )

    analytics_selection = build_dbt_asset_selection(
        [dbt_gold_analytics],
        dbt_select="tag:game",
    )

    all_game_selection = staging_selection | core_selection | analytics_selection

    game_bets_pipeline_job = define_asset_job(
        name="game_bets_pipeline_job",
        selection=all_game_selection,
        tags={"audience": "internal", "domain": "game", "pii": "false"},
        description="Daily pipeline for game bets analytics: staging -> core -> gold",
    )

    game_bets_pipeline_schedule = ScheduleDefinition(
        name="game_bets_pipeline_schedule",
        job=game_bets_pipeline_job,
        cron_schedule="0 6 * * *",  # 6:00 AM UTC daily
    )
else:
    game_bets_pipeline_job = None
    game_bets_pipeline_schedule = None
