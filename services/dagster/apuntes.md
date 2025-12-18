# Dagster Best Practices & Project Structure

## Scratch Code

```
uvx create-dagster@latest project dagster

cd dagster

uv sync
uv add polars boto3

dg scaffold defs dagster.asset assets.py

mkdir src/dagster/defs/data && touch src/dagster/defs/data/sample_data.csv

dg list defs
dg check defs
```

## Recommended Folder Structure

```
src/dagster_project/
├── __init__.py
├── definitions.py          # The "mothership" - wires everything together
├── dbt_config.py           # dbt project configuration (if using dbt)
├── assets/                 # All assets organized by domain/source
│   ├── __init__.py
│   ├── api_assets.py
│   └── dbt_assets.py
├── jobs/                   # Jobs and their schedules (colocated)
│   ├── __init__.py
│   └── sync_users.py
└── resources/              # Shared infrastructure (DB connections, API clients)
    ├── __init__.py
    └── postgres.py
```

## Core Concepts

### definitions.py - The Mothership

Single entry point that tells Dagster everything the project contains:

```python
from dagster import Definitions, load_assets_from_modules

defs = Definitions(
    assets=[...],       # What data exists
    jobs=[...],         # How to run groups of assets
    schedules=[...],    # When to run jobs
    sensors=[...],      # Triggers based on events
    resources={...},    # Shared infrastructure
)
```

- `load_assets_from_modules()` auto-discovers all `@asset` decorated functions, so you just keep adding files to `assets/` and they get picked up.

### Assets vs Ops

|            | Assets             | Ops                         |
| ---------- | ------------------ | --------------------------- |
| Focus      | _What_ data exists | _What_ code runs            |
| Lineage    | Automatic tracking | Manual                      |
| Idempotent | By design          | Up to you                   |
| UI         | Shows data catalog | Shows execution graph       |
| Use case   | Data pipelines     | One-off tasks, side effects |

- Use assets for: ETL/ELT, dbt models, ML features/models, anything where you care about output data.
- Use ops for: Sending notifications, triggering external systems, cleanup tasks, side effects with no data artifact.

Dagster's direction is assets-first. Prefer assets unless you have a clear reason for ops.

## Example Patterns

### Resource Definition

```python
# resources/postgres.py
from dagster import ConfigurableResource
from contextlib import contextmanager
import psycopg2

class PostgresResource(ConfigurableResource):
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    database: str = "postgres"
    schema_: str = "public"  # trailing underscore because `schema` is reserved

    @contextmanager
    def get_connection(self):
        conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            options=f"-c search_path={self.schema_}",
        )
        try:
            yield conn
        finally:
            conn.close()
```

### Asset Definition

```python
# assets/api_assets.py
import requests
from dagster import asset, AssetExecutionContext
from dagster_project.resources import PostgresResource

@asset
def api_users(context: AssetExecutionContext) -> list[dict]:
    """Fetch users from API."""
    response = requests.get("https://jsonplaceholder.typicode.com/users")
    response.raise_for_status()
    users = response.json()
    context.log.info(f"Fetched {len(users)} users")
    return users

@asset
def users_in_postgres(
    context: AssetExecutionContext,
    api_users: list[dict],
    postgres: PostgresResource,
) -> None:
    """Store users in Postgres."""
    with postgres.get_connection() as conn:
        with conn.cursor() as cur:
            # Create table, insert data, etc.
            conn.commit()
```

### Job + Schedule (Colocated)

```python
# jobs/sync_users.py
from dagster import (
    define_asset_job,
    AssetSelection,
    ScheduleDefinition,
    DefaultScheduleStatus,
)

sync_users_job = define_asset_job(
    name="sync_users_job",
    selection=AssetSelection.assets("api_users", "users_in_postgres"),
    description="Fetches users from API and loads to Postgres",
)

sync_users_schedule = ScheduleDefinition(
    job=sync_users_job,
    cron_schedule="0 12 * * *",  # 12:00 PM UTC daily
    execution_timezone="UTC",
    default_status=DefaultScheduleStatus.RUNNING,  # auto-enable
)
```

### Module Exports

```python
# jobs/__init__.py
from .sync_users import sync_users_job, sync_users_schedule

__all__ = ["sync_users_job", "sync_users_schedule"]
```

## CLI Commands

```bash
# Start local development server
dagster dev

# Validate definitions
dagster definitions validate

# Quick Python check
python -c "from dagster_project.definitions import defs; print(defs.get_all_schedules())"
```

`dg dev` starts the Dagster UI at `http://localhost:3000` by default.

## dbt Integration

For full dbt integration, Dagster needs direct access to dbt project files. Common setups:

Monorepo (recommended):

```
repo/
├── dagster/
│   └── src/dagster_project/
└── dbt/
    ├── dbt_project.yml
    ├── models/
    └── target/manifest.json
```

dbt inside Dagster project:

```
dagster_project/
├── src/dagster_project/
└── dbt/
    └── ...
```

The integration gives you automatic asset creation from dbt models, lineage tracking, and ability to run `dbt build` within Dagster pipelines natively.

## potentailly easier resource / job / schedule cleanup

```py
import pkgutil
import importlib
from dagster import Definitions, load_assets_from_package_module

from dagster_project import assets, jobs, schedules

def collect_from_package(package, attr_type):
    """Collect all objects of a given type from a package."""
    items = []
    for _, name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        module = importlib.import_module(name)
        for attr in dir(module):
            obj = getattr(module, attr)
            if isinstance(obj, attr_type):
                items.append(obj)
    return items

defs = Definitions(
    assets=load_assets_from_package_module(assets),
    jobs=collect_from_package(jobs, JobDefinition),
    schedules=collect_from_package(schedules, ScheduleDefinition),
)

```
