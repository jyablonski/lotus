from dagster_project.defs.assets.transformations.dbt_assets import (
    dbt_gold_analytics,
    dbt_silver_core,
    dbt_silver_stg,
)
from dagster_project.defs.jobs.utils import (
    Audience,
    Domain,
    create_job,
    dbt_tag_selection,
)

all_game_selection = dbt_tag_selection(
    [dbt_silver_stg, dbt_silver_core, dbt_gold_analytics],
    tag="game",
)

if all_game_selection is not None:
    game_bets_pipeline_job, game_bets_pipeline_schedule = create_job(
        name="game_bets_pipeline_job",
        selection=all_game_selection,
        audience=Audience.INTERNAL,
        domain=Domain.GAME,
        pii=False,
        schedule="0 6 * * *",  # 6:00 AM UTC daily
        description="Daily pipeline for game bets analytics: staging -> core -> gold",
    )
else:
    game_bets_pipeline_job = None
    game_bets_pipeline_schedule = None
