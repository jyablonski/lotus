"""Dagster definitions entry point.

Assets are auto-discovered from the assets/ package via load_assets_from_package_module.
Jobs and schedules are auto-discovered from the jobs/ package — just drop a file there.
Resources are explicitly registered in resources/RESOURCES.
"""

import importlib
import pkgutil

from dagster import (
    Definitions,
    JobDefinition,
    ScheduleDefinition,
    SensorDefinition,
    load_asset_checks_from_package_module,
    load_assets_from_package_module,
)
from dagster._core.definitions.unresolved_asset_job_definition import (
    UnresolvedAssetJobDefinition,
)
from dagster_dbt import DbtCliResource

from dagster_project import assets, jobs, sensors
from dagster_project.dbt_config import DBT_PROFILES_DIR, dbt_project
from dagster_project.resources import RESOURCES

_JOB_TYPES = (JobDefinition, UnresolvedAssetJobDefinition)


def _collect_from_package(package, types: tuple[type, ...]) -> list:
    """Walk every module in *package* and return all top-level objects matching *types*.

    Filters out None values so conditional definitions (e.g. dbt_pipeline_job = None)
    don't break registration.
    """
    results = []
    for _importer, module_name, _ispkg in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"{package.__name__}.{module_name}")
        for obj in vars(module).values():
            if isinstance(obj, types) and obj is not None:
                results.append(obj)
    return results


all_jobs = _collect_from_package(jobs, _JOB_TYPES)
all_schedules = _collect_from_package(jobs, (ScheduleDefinition,))
all_sensors = _collect_from_package(sensors, (SensorDefinition,))

all_resources = dict(RESOURCES)

if dbt_project is not None:
    all_resources["dbt"] = DbtCliResource(
        project_dir=dbt_project,
        profiles_dir=DBT_PROFILES_DIR,
    )

defs = Definitions(
    assets=load_assets_from_package_module(assets),
    asset_checks=load_asset_checks_from_package_module(assets),
    jobs=all_jobs,
    schedules=all_schedules,
    sensors=all_sensors,
    resources=all_resources,
)
