from dagster_project.assets.ingestion.get_game_types_from_api import (
    get_game_types_from_api,
)
from dagster_project.jobs.utils import Audience, Domain, create_job

get_game_types_job = create_job(
    name="get_game_types_job",
    assets=[get_game_types_from_api],
    audience=Audience.INTERNAL,
    domain=Domain.GAME,
    pii=False,
)
