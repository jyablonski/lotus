import os
from pathlib import Path

from dagster_dbt import DbtProject

# In the container, this resolves to /app/dbt (three levels up from this file).
DBT_PROJECT_DIR = Path(__file__).parent.parent.parent / "dbt"
DBT_PROFILES_DIR = DBT_PROJECT_DIR / "profiles"

# Skip initialization when the dbt project isn't mounted (e.g. unit tests that
# only import dagster_project). Tests can still import this module safely.
if DBT_PROJECT_DIR.exists() and DBT_PROJECT_DIR.is_dir():
    # DBT_PROFILES_DIR must be set in the environment for prepare_if_dev() and
    # any subsequent dbt invocations to find the profiles file.
    os.environ["DBT_PROFILES_DIR"] = str(DBT_PROFILES_DIR)

    dbt_project = DbtProject(
        project_dir=DBT_PROJECT_DIR,
        packaged_project_dir=Path(__file__).parent / "dbt_project",
    )

    dbt_project.prepare_if_dev()
else:
    dbt_project = None
