from dagster import define_asset_job, AssetSelection, ScheduleDefinition

sync_users_job = define_asset_job(
    name="sync_users_job",
    selection=AssetSelection.assets("api_users", "users_in_postgres"),
)

sync_users_schedule = ScheduleDefinition(
    job=sync_users_job,
    cron_schedule="0 12 * * *",  # 12:00 PM UTC daily
)
