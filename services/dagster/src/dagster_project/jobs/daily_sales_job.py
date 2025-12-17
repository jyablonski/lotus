from dagster import define_asset_job, AssetSelection, ScheduleDefinition

daily_sales_job = define_asset_job(
    name="daily_sales_job",
    selection=AssetSelection.assets("sales_summary").upstream(),
)

daily_sales_schedule = ScheduleDefinition(
    name="daily_sales_schedule",
    job=daily_sales_job,
    cron_schedule="0 1,13 * * *",  # 1:00 AM and 1:00 PM UTC daily
)
