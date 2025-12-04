import os
from pathlib import Path
from dagster_dbt import DbtProject

RELATIVE_PATH_TO_DBT = "../../../../dbt"
DBT_PROJECT_DIR = Path(__file__).joinpath(RELATIVE_PATH_TO_DBT).resolve()

# 1. Define the specific path to your profiles directory
DBT_PROFILES_DIR = DBT_PROJECT_DIR / "profiles"

# 2. CRITICAL: Set the Environment Variable
# This tells 'prepare_if_dev' (and dbt globally) where to look
os.environ["DBT_PROFILES_DIR"] = str(DBT_PROFILES_DIR)

dbt_project = DbtProject(
    project_dir=DBT_PROJECT_DIR,
    packaged_project_dir=Path(__file__).parent / "dbt_project",
)

# Now this will work because it sees the env var
dbt_project.prepare_if_dev()
