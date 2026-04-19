from dagster import AssetSelection, ScheduleDefinition, define_asset_job

incremental_example_api_job = define_asset_job(
    name="incremental_example_api_job",
    selection=AssetSelection.assets("example_api_records_incremental"),
    tags={"audience": "internal", "domain": "ingestion", "pii": "false"},
    description=(
        "Daily example API ingestion that uses source.ingestion_watermarks "
        "to pull records incrementally by modified_at."
    ),
)

incremental_example_api_schedule = ScheduleDefinition(
    name="incremental_example_api_daily_schedule",
    job=incremental_example_api_job,
    cron_schedule="0 6 * * *",
    execution_timezone="America/Los_Angeles",
)
