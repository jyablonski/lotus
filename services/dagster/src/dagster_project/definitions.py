import os
from dagster import Definitions, load_assets_from_modules
from dagster_dbt import DbtCliResource

from dagster_project import assets
from dagster_project.jobs import hello_world_job, sync_users_job, sync_users_schedule
from dagster_project.resources import PostgresResource
from dagster_project.dbt_config import dbt_project, DBT_PROFILES_DIR

all_assets = load_assets_from_modules([assets])

# Build resources dict conditionally based on dbt_project availability
resources = {
    "postgres": PostgresResource(
        host=os.getenv("DAGSTER_POSTGRES_HOST", "postgres"),
        port=int(os.getenv("DAGSTER_POSTGRES_PORT", "5432")),
        user=os.getenv("DAGSTER_POSTGRES_USER", "postgres"),
        password=os.getenv("DAGSTER_POSTGRES_PASSWORD", "postgres"),
        database=os.getenv("DAGSTER_POSTGRES_DB", "postgres"),
        schema_="source",
    ),
}

# Only add dbt resource if dbt_project is available
if dbt_project is not None:
    resources["dbt"] = DbtCliResource(
        project_dir=dbt_project,
        profiles_dir=DBT_PROFILES_DIR,
    )

defs = Definitions(
    assets=all_assets,
    jobs=[sync_users_job, hello_world_job],
    schedules=[sync_users_schedule],
    resources=resources,
)
