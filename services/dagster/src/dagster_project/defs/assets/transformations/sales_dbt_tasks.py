from dagster_project.dbt_pipeline import build_dbt_source_pipeline
from dagster_project.defs.assets.ingestion.get_sales_data import sales_data_bronze

REVENUE_SOURCE_NAME = "revenue"

sales_pipeline = build_dbt_source_pipeline(
    data_source=REVENUE_SOURCE_NAME,
    bronze_asset=sales_data_bronze,
)

# Bind each step at module scope so Dagster's defs-folder autoloader registers
# them. ``None`` when the dbt project/manifest isn't available (e.g. unit tests),
# or when a layer has no matching tagged models; the autoloader ignores ``None``.
revenue_dbt_source_freshness = (
    sales_pipeline.source_freshness if sales_pipeline else None
)
revenue_dbt_source_tests = sales_pipeline.source_tests if sales_pipeline else None
revenue_dbt_silver_build = sales_pipeline.silver_build if sales_pipeline else None
revenue_dbt_gold_build = sales_pipeline.gold_build if sales_pipeline else None
