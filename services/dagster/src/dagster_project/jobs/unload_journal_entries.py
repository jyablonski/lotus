from dagster import AssetSelection, define_asset_job

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
unload_journal_entries_job = define_asset_job(
    name="unload_journal_entries_job",
    selection=AssetSelection.assets("unload_journals_to_s3"),
    hooks=unload_notification_hooks,
)
