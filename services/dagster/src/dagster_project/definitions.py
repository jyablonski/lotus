from dagster import Definitions, load_assets_from_modules
from dagster_dbt import DbtCliResource
from . import assets

from .dbt_config import dbt_project, DBT_PROFILES_DIR

all_assets = load_assets_from_modules([assets])

defs = Definitions(
    assets=all_assets,
    resources={
        "dbt": DbtCliResource(
            project_dir=dbt_project,
            profiles_dir=DBT_PROFILES_DIR,
        ),
    },
)
