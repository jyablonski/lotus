from dagster_project.defs.assets.catalog.openmetadata_glossary_sync import (
    openmetadata_glossary_sync,
)
from dagster_project.defs.jobs.utils import Audience, Domain, create_job

openmetadata_glossary_sync_job = create_job(
    name="openmetadata_glossary_sync_job",
    assets=[openmetadata_glossary_sync],
    audience=Audience.INTERNAL,
    domain=Domain.OPS,
    pii=False,
)
