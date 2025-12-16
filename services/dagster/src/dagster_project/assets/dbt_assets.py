from dagster import AssetExecutionContext
from dagster_dbt import DbtCliResource, dbt_assets

from dagster_project.dbt_config import dbt_project


@dbt_assets(manifest=dbt_project.manifest_path)
def dbt_analytics(context: AssetExecutionContext, dbt: DbtCliResource):
    # This runs `dbt build` for the selected assets
    # It passes the correct flags to run only the specific models Dagster requested
    yield from dbt.cli(["build"], context=context).stream()
