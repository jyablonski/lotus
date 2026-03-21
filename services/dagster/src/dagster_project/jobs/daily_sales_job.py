from dagster import (
    AssetSelection,
    ScheduleDefinition,
    define_asset_job,
)

daily_sales_job = define_asset_job(
    name="daily_sales_job",
    selection=AssetSelection.assets("sales_data"),
    tags={"audience": "internal", "domain": "analytics", "pii": "false"},
)

daily_sales_schedule = ScheduleDefinition(
    job=daily_sales_job,
    cron_schedule="0 12 * * *",  # 12:00 PM UTC daily
)
