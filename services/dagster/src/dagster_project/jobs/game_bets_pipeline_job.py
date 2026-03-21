from dagster import ScheduleDefinition, define_asset_job
from dagster_dbt import build_dbt_asset_selection

from dagster_project.assets.transformations.dbt_assets import dbt_analytics

if dbt_analytics is not None:
    # Select only game-related dbt models by name
    staging_selection = build_dbt_asset_selection(
        [dbt_analytics],
        dbt_select="stg_user_game_bets stg_user_game_balances",
    )

    core_selection = build_dbt_asset_selection(
        [dbt_analytics],
        dbt_select="fct_game_bets",
    )

    analytics_selection = build_dbt_asset_selection(
        [dbt_analytics],
        dbt_select="user_game_summary",
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
