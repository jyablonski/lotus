from dagster import AssetExecutionContext
from dagster_dbt import DbtCliResource, dbt_assets

from dagster_project.dbt_config import dbt_project

# Only define dbt_analytics if dbt_project is available
# This allows tests to import the module without requiring the dbt project
if dbt_project is not None:

    @dbt_assets(manifest=dbt_project.manifest_path)
    def dbt_analytics(context: AssetExecutionContext, dbt: DbtCliResource):
        # This runs `dbt build` for the selected assets
        # It passes the correct flags to run only the specific models Dagster requested
        yield from dbt.cli(["build"], context=context).stream()
else:
    # Define dbt_analytics as None when dbt_project is not available
    dbt_analytics = None
