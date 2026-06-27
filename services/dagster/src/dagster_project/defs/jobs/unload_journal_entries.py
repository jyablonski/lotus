from dagster_project.defs.assets.exports.unload_journals_to_s3 import (
    unload_journals_to_s3,
)
from dagster_project.defs.jobs.utils import Audience, Domain, create_job
from dagster_project.ops.slack_hooks import create_slack_notification_hooks

# Create reusable Slack notification hooks for the unload job
# These hooks will send ✅ on success and ❌ on failure
unload_notification_hooks = create_slack_notification_hooks(
    asset_name="unload_journals_to_s3",
    success_message="✅ Journal entries unload completed successfully!",
    failure_message="❌ Journal entries unload failed!",
)

# Define the asset job with success/failure notification hooks
# use case here is to send a custom slack message
unload_journal_entries_job = create_job(
    name="unload_journal_entries_job",
    assets=[unload_journals_to_s3],
    audience=Audience.INTERNAL,
    domain=Domain.ANALYTICS,
    pii=True,
    hooks=unload_notification_hooks,
)
