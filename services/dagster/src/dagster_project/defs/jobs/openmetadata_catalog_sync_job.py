from dagster_project.defs.assets.catalog.openmetadata_sync import (
    openmetadata_dbt_sync,
    openmetadata_postgres_sync,
)
from dagster_project.defs.jobs.utils import Audience, Domain, create_job

openmetadata_catalog_sync_job, openmetadata_catalog_sync_schedule = create_job(
    name="openmetadata_catalog_sync_job",
    assets=[openmetadata_postgres_sync, openmetadata_dbt_sync],
    audience=Audience.INTERNAL,
    domain=Domain.OPS,
    pii=False,
    schedule="0 14 * * *",  # 2:00 PM UTC daily, after the other dbt builds
)
