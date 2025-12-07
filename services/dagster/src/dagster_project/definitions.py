from dagster import Definitions, load_assets_from_modules
from dagster_dbt import DbtCliResource

from dagster_project import assets
from dagster_project.jobs import sync_users_job, sync_users_schedule
from dagster_project.resources import PostgresResource
from dagster_project.dbt_config import dbt_project, DBT_PROFILES_DIR

all_assets = load_assets_from_modules([assets])

defs = Definitions(
    assets=all_assets,
    jobs=[sync_users_job],
    schedules=[sync_users_schedule],
    resources={
        "dbt": DbtCliResource(
            project_dir=dbt_project,
            profiles_dir=DBT_PROFILES_DIR,
        ),
        "postgres": PostgresResource(
            host="localhost",
            port=5432,
            user="postgres",
            password="postgres",
            database="postgres",
            schema_="source",
        ),
    },
)
