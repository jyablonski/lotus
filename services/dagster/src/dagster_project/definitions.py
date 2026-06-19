"""Dagster definitions entry point.

Assets are auto-discovered from the assets/ package via an explicit module walk.
Jobs and schedules are auto-discovered from the jobs/ package; demo/example modules
are excluded unless DAGSTER_INCLUDE_EXAMPLES is true.
Resources are explicitly registered in resources/RESOURCES.
"""

import importlib
import os
import pkgutil
from types import ModuleType

from dagster import (
    Definitions,
    JobDefinition,
    ScheduleDefinition,
    SensorDefinition,
    load_asset_checks_from_modules,
    load_assets_from_modules,
)
from dagster._core.definitions.unresolved_asset_job_definition import (
    UnresolvedAssetJobDefinition,
)
from dagster_dbt import DbtCliResource

from dagster_project import assets, jobs, sensors
from dagster_project.dbt_config import DBT_PROFILES_DIR, dbt_project
from dagster_project.resources import RESOURCES

_JOB_TYPES = (JobDefinition, UnresolvedAssetJobDefinition)
_TRUTHY_ENV_VALUES = {"1", "true", "yes", "on"}

_EXAMPLE_ASSET_MODULES = {
    "dagster_project.assets.ingestion.example_assets",
    "dagster_project.assets.ingestion.get_api_assets",
    "dagster_project.assets.ingestion.incremental_example_api",
}
_EXAMPLE_JOB_MODULES = {
    "dagster_project.jobs.example_job",
    "dagster_project.jobs.incremental_example_api_job",
    "dagster_project.jobs.sync_users_job",
}


def _include_examples() -> bool:
    return os.getenv("DAGSTER_INCLUDE_EXAMPLES", "").lower() in _TRUTHY_ENV_VALUES


def _collect_modules(
    package: ModuleType,
    *,
    exclude_modules: set[str] | None = None,
) -> list[ModuleType]:
    """Import every non-package module in *package*, optionally skipping examples."""
    exclude_modules = exclude_modules or set()
    modules = []
    prefix = f"{package.__name__}."
    for module_info in pkgutil.walk_packages(package.__path__, prefix):
        if module_info.ispkg or module_info.name in exclude_modules:
            continue
        modules.append(importlib.import_module(module_info.name))
    return modules


def _collect_from_modules(modules: list[ModuleType], types: tuple[type, ...]) -> list:
    """Return all top-level objects in *modules* that match *types*.

    Filters out None values so conditional definitions (e.g. dbt_pipeline_job = None)
    don't break registration.
    """
    results = []
    for module in modules:
        for obj in vars(module).values():
            if isinstance(obj, types) and obj is not None:
                results.append(obj)
    return results


asset_modules = _collect_modules(
    assets,
    exclude_modules=set() if _include_examples() else _EXAMPLE_ASSET_MODULES,
)
job_modules = _collect_modules(
    jobs,
    exclude_modules=set() if _include_examples() else _EXAMPLE_JOB_MODULES,
)
sensor_modules = _collect_modules(sensors)

all_jobs = _collect_from_modules(job_modules, _JOB_TYPES)
all_schedules = _collect_from_modules(job_modules, (ScheduleDefinition,))
all_sensors = _collect_from_modules(sensor_modules, (SensorDefinition,))

all_resources = dict(RESOURCES)

if dbt_project is not None:
    all_resources["dbt"] = DbtCliResource(
        project_dir=dbt_project,
        profiles_dir=DBT_PROFILES_DIR,
    )

defs = Definitions(
    assets=load_assets_from_modules(asset_modules),
    asset_checks=load_asset_checks_from_modules(asset_modules),
    jobs=all_jobs,
    schedules=all_schedules,
    sensors=all_sensors,
    resources=all_resources,
)
