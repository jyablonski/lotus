from dagster import AssetExecutionContext
from dagster_dbt import DbtCliResource, dbt_assets

from dagster_project.dbt_config import dbt_project

# Split dbt assets into one definition per layer so Dagster runs each as a
# separate op/step, giving visibility in the Gantt chart.
# Only defined when dbt_project is available (test resilience).
if dbt_project is not None:

    @dbt_assets(
        manifest=dbt_project.manifest_path, select="tag:staging", name="dbt_silver_stg"
    )
    def dbt_silver_stg(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    @dbt_assets(
        manifest=dbt_project.manifest_path, select="tag:core", name="dbt_silver_core"
    )
    def dbt_silver_core(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    @dbt_assets(
        manifest=dbt_project.manifest_path,
        select="tag:analytics",
        name="dbt_gold_analytics",
    )
    def dbt_gold_analytics(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

else:
    dbt_silver_stg = None
    dbt_silver_core = None
    dbt_gold_analytics = None
