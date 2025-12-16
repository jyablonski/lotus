from dagster import AssetExecutionContext
from dagster_dbt import DbtCliResource, dbt_assets

from dagster_project.dbt_config import get_manifest_path

# Only define dbt_analytics if manifest exists
# This allows the module to be imported in tests without requiring manifest
# In production, the manifest should be packaged via 'dagster-dbt project prepare-and-package'
_manifest_path = get_manifest_path()

if _manifest_path is not None:

    @dbt_assets(manifest=_manifest_path)
    def dbt_analytics(context: AssetExecutionContext, dbt: DbtCliResource):
        # This runs `dbt build` for the selected assets
        # It passes the correct flags to run only the specific models Dagster requested
        yield from dbt.cli(["build"], context=context).stream()
# If manifest doesn't exist, dbt_analytics simply won't be defined
# load_assets_from_modules will skip it automatically
