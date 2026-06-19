from dagster_project.assets.ingestion.get_sales_data import sales_data
from dagster_project.jobs.utils import Audience, Domain, create_job

daily_sales_job, daily_sales_schedule = create_job(
    name="daily_sales_job",
    assets=[sales_data],
    audience=Audience.INTERNAL,
    domain=Domain.ANALYTICS,
    pii=False,
    schedule="0 12 * * *",  # 12:00 PM UTC daily
)
