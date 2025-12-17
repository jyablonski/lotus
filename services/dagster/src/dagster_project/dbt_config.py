import os
from pathlib import Path
from dagster_dbt import DbtProject

# Calculate path to dbt project
# From /app/src/dagster_project/dbt_config.py:
# Path(__file__) = /app/src/dagster_project/dbt_config.py
# Path(__file__).parent = /app/src/dagster_project/
# Path(__file__).parent.parent = /app/src/
# Path(__file__).parent.parent.parent = /app/
# So /app/dbt
DBT_PROJECT_DIR = Path(__file__).parent.parent.parent / "dbt"

# 1. Define the specific path to your profiles directory
DBT_PROFILES_DIR = DBT_PROJECT_DIR / "profiles"

# Initialize dbt_project only if the directory exists
# This allows tests to import the module without requiring the dbt project
if DBT_PROJECT_DIR.exists() and DBT_PROJECT_DIR.is_dir():
    # 2. CRITICAL: Set the Environment Variable
    # This tells 'prepare_if_dev' (and dbt globally) where to look
    os.environ["DBT_PROFILES_DIR"] = str(DBT_PROFILES_DIR)

    dbt_project = DbtProject(
        project_dir=DBT_PROJECT_DIR,
        packaged_project_dir=Path(__file__).parent / "dbt_project",
    )

    dbt_project.prepare_if_dev()
else:
    # Set dbt_project to None if directory doesn't exist
    # This allows tests to import the module without errors
    dbt_project = None
