from dagster_project.defs.assets.ingestion.get_sales_data import (
    sales_data,
    sales_data_bronze,
)
from dagster_project.defs.assets.transformations.sales_dbt_tasks import (
    sales_data_dbt_gold_build,
    sales_data_dbt_silver_build,
    sales_data_dbt_source_freshness,
    sales_data_dbt_source_tests,
)
from dagster_project.defs.jobs.utils import Audience, Domain, create_job

sales_pipeline_assets = [
    sales_data,
    sales_data_bronze,
    *[
        asset_def
        for asset_def in (
            sales_data_dbt_source_freshness,
            sales_data_dbt_source_tests,
            sales_data_dbt_silver_build,
            sales_data_dbt_gold_build,
        )
        if asset_def is not None
    ],
]

daily_sales_job, daily_sales_schedule = create_job(
    name="daily_sales_job",
    assets=sales_pipeline_assets,
    audience=Audience.INTERNAL,
    domain=Domain.ANALYTICS,
    pii=False,
    schedule="0 12 * * *",  # 12:00 PM UTC daily
)
