from dagster_project.defs.assets.exports.sync_flags_to_sheets import (
    get_feature_flags_from_postgres,
    sync_flags_to_sheets,
)
from dagster_project.defs.jobs.utils import Audience, Domain, create_job

sync_flags_to_sheets_job = create_job(
    name="sync_flags_to_sheets_job",
    assets=[get_feature_flags_from_postgres, sync_flags_to_sheets],
    audience=Audience.INTERNAL,
    domain=Domain.OPS,
    pii=False,
    description="Sync feature flags from Postgres source.feature_flags table to Google Sheets",
)
