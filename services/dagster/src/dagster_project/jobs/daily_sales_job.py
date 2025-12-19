from dagster import AssetSelection, build_schedule_from_partitioned_job, define_asset_job

from dagster_project.assets.ingestion.get_sales_data import daily_partitions

# Define the job with dependency chain: sales_data -> sales_data_asset_check -> sales_summary
# Note: Asset checks run automatically when their associated asset materializes.
# With blocking=True, sales_summary will only run if the check passes.
daily_sales_job = define_asset_job(
    name="daily_sales_job",
    selection=AssetSelection.assets("sales_data", "sales_summary"),
    partitions_def=daily_partitions,
)

# Use build_schedule_from_partitioned_job instead of ScheduleDefinition because:
# - It automatically handles partition selection (defaults to previous day's partition)
# - Ensures the schedule runs the correct partition without manual cron logic
# - Simplifies partition-aware scheduling for daily partitioned jobs
daily_sales_schedule = build_schedule_from_partitioned_job(
    daily_sales_job,
    hour_of_day=12,  # 12:00 PM UTC
    minute_of_hour=0,
)
