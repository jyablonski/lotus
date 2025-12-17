# import all jobs and schedules within this folder
# if added here, they will automatically be pulled into the definitions.py file
# and be available in the Dagster UI
from .daily_sales_job import daily_sales_job, daily_sales_schedule
from .sync_users_job import sync_users_job, sync_users_schedule
from .example_job import hello_world_job
from .example_job_v3 import hello_world_job_v3

__all__ = [
    "daily_sales_job",
    "daily_sales_schedule",
    "sync_users_job",
    "sync_users_schedule",
    "hello_world_job",
    "hello_world_job_v3",
]
