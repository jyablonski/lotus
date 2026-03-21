from dagster import AssetSelection, ScheduleDefinition, define_asset_job

sync_users_job = define_asset_job(
    name="sync_users_job",
    selection=AssetSelection.assets("get_api_users", "users_in_postgres"),
    tags={"audience": "internal", "domain": "ops", "pii": "true"},
)

sync_users_schedule = ScheduleDefinition(
    name="sync_users_schedule",
    job=sync_users_job,
    cron_schedule="0 12 * * *",  # 12:00 PM UTC daily
)
