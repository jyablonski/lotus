from dagster_project.defs.examples.assets.ingestion.example_assets import (
    hello_world_asset,
)
from dagster_project.defs.jobs.utils import Audience, Domain, create_job

hello_world_job = create_job(
    name="hello_world_example_job",
    assets=[hello_world_asset],
    audience=Audience.INTERNAL,
    domain=Domain.OPS,
    pii=False,
)
