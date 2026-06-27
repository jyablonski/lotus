from dagster_project.defs.examples.assets.ingestion.get_api_assets import (
    get_api_users,
    users_in_postgres,
)
from dagster_project.defs.jobs.utils import Audience, Domain, create_job

sync_users_job, sync_users_schedule = create_job(
    name="sync_users_job",
    assets=[get_api_users, users_in_postgres],
    audience=Audience.INTERNAL,
    domain=Domain.OPS,
    pii=True,
    schedule="0 12 * * *",  # 12:00 PM UTC daily
)
