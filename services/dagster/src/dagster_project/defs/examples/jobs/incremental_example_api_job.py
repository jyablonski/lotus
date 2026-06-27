from dagster_project.defs.examples.assets.ingestion.incremental_example_api import (
    example_api_records_incremental,
)
from dagster_project.defs.jobs.utils import Audience, Domain, create_job

incremental_example_api_job, incremental_example_api_schedule = create_job(
    name="incremental_example_api_job",
    assets=[example_api_records_incremental],
    audience=Audience.INTERNAL,
    domain=Domain.INGESTION,
    pii=False,
    schedule="0 6 * * *",
    execution_timezone="America/Los_Angeles",
    description=(
        "Daily example API ingestion that uses source.ingestion_watermarks "
        "to pull records incrementally by modified_at."
    ),
)
