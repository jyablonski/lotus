from dagster import (
    ConfigurableResource,
    Definitions,
    JobDefinition,
    ResourceDefinition,
    ScheduleDefinition,
    load_assets_from_package_module,
)
from dagster._core.definitions.unresolved_asset_job_definition import (
    UnresolvedAssetJobDefinition,
)
from dagster_dbt import DbtCliResource

from dagster_project import (
    assets,
    jobs,
    resources as resources_module,
)
from dagster_project.dbt_config import DBT_PROFILES_DIR, dbt_project


def load_resources() -> dict:
    """Auto-discover all ConfigurableResource instances from resources module."""
    resource_dict = {}
    for name, obj in vars(resources_module).items():
        if isinstance(obj, (ConfigurableResource, ResourceDefinition)):
            # Use snake_case name as key
            resource_dict[name.lower()] = obj
    return resource_dict


# Grab all jobs and schedules from the jobs module
all_jobs = [
    obj
    for obj in vars(jobs).values()
    if isinstance(obj, (JobDefinition, UnresolvedAssetJobDefinition))
]
all_schedules = [obj for obj in vars(jobs).values() if isinstance(obj, ScheduleDefinition)]

all_resources = load_resources()


# Only add dbt resource if dbt_project is available
if dbt_project is not None:
    all_resources["dbt"] = DbtCliResource(
        project_dir=dbt_project,
        profiles_dir=DBT_PROFILES_DIR,
    )

defs = Definitions(
    assets=load_assets_from_package_module(assets),
    jobs=all_jobs,
    schedules=all_schedules,
    resources=all_resources,
)
