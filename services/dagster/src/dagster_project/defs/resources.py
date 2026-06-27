from dagster import Definitions
from dagster_dbt import DbtCliResource

from dagster_project.dbt_config import DBT_PROFILES_DIR, dbt_project
from dagster_project.resources import RESOURCES

all_resources = dict(RESOURCES)

if dbt_project is not None:
    all_resources["dbt"] = DbtCliResource(
        project_dir=dbt_project,
        profiles_dir=DBT_PROFILES_DIR,
    )

resource_defs = Definitions(resources=all_resources)
