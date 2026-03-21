---
name: dagster-asset
description: >
  Step-by-step workflow for adding new Dagster assets, resources, and jobs to the Lotus
  data pipeline. Covers auto-discovery of assets, manual resource registration, job/schedule
  definitions, dbt asset integration, and the SQL query pattern. Use this skill whenever
  the user wants to add a new Dagster asset, resource, job, schedule, or asks how the
  Dagster project's auto-import and resource registration works.
---

# Dagster Asset Workflow

Source code: `services/dagster/src/dagster_project/` | Entry point: `definitions.py`

## Auto-Discovery vs Manual Registration

| Component     | Auto-discovered? | How to add                                         |
| ------------- | ---------------- | -------------------------------------------------- |
| Assets        | Yes              | Create file in `assets/`                           |
| Jobs          | Yes              | Create file in `jobs/`                             |
| Schedules     | Yes              | Define alongside the job                           |
| Sensors       | Yes              | Create file in `sensors/`                          |
| **Resources** | **No**           | Add to `RESOURCES` dict in `resources/__init__.py` |

Assets are found via `load_assets_from_package_module(assets)`. Jobs/schedules are found via `jobs/__init__.py` auto-importing all modules, then `_collect_from_package()` collecting top-level definitions. **Resources must be explicitly registered.**

---

## Adding a New Asset

Create a file in the appropriate subdirectory (`assets/ingestion/`, `assets/transformations/`, `assets/exports/`, `assets/internal/`):

```python
from dagster import AssetExecutionContext, asset
from dagster_project.resources import PostgresResource

@asset(group_name="ingestion")
def get_my_data(context: AssetExecutionContext) -> list[dict]:
    """Fetch data from an external API."""
    import requests
    response = requests.get("https://api.example.com/data")
    response.raise_for_status()
    return response.json()

@asset(group_name="ingestion")
def my_data_in_postgres(
    context: AssetExecutionContext,
    get_my_data: list[dict],           # dependency by parameter name
    postgres_conn: PostgresResource,    # resource injection by RESOURCES key
) -> None:
    with postgres_conn.get_connection() as conn, conn.cursor() as cur:
        for record in get_my_data:
            cur.execute("INSERT INTO ...", (record["id"], record["name"]))
        conn.commit()
```

That's it -- auto-discovered, no registration needed.

### Other asset patterns

```python
# Explicit dependency on a dbt model
@asset(deps=[AssetKey(["gold", "user_journal_summary"])])
def export_summary(...): ...

# Partitioned asset
daily_partitions = DailyPartitionsDefinition(start_date="2025-12-18")
@asset(group_name="ingestion", partitions_def=daily_partitions)
def daily_data(context): partition_date = context.partition_key

# Freshness + ownership
@asset(group_name="exports", owners=["team:data-engineering"],
       freshness_policy=FreshnessPolicy.time_window(fail_window=timedelta(hours=24)))
def monitored_asset(...): ...

# Output metadata
context.add_output_metadata({"num_rows": len(df)})
```

---

## Adding a New Resource

Resources are **NOT auto-discovered**. Three steps required:

**1. Create** `resources/my_resource.py`:

```python
from dagster import ConfigurableResource, EnvVar

class MyResource(ConfigurableResource):
    api_key: str
    base_url: str = "https://api.example.com"

    def get_client(self):
        import requests
        session = requests.Session()
        session.headers["Authorization"] = f"Bearer {self.api_key}"
        return session

my_resource = MyResource(api_key=EnvVar("MY_RESOURCE_API_KEY"), base_url=EnvVar("MY_RESOURCE_BASE_URL"))
```

**2. Register** in `resources/__init__.py` -- key must match the parameter name assets use:

```python
from .my_resource import MyResource, my_resource

RESOURCES: dict = {
    # ... existing ...
    "my_resource": my_resource,   # assets inject via: def my_asset(my_resource: MyResource)
}
```

**3. Add env vars** to `docker/docker-compose-local.yaml` under the dagster service.

---

## Adding a New Job

Create `jobs/my_job.py` -- auto-discovered, no registration needed:

```python
from dagster import AssetSelection, ScheduleDefinition, define_asset_job

my_job = define_asset_job(
    name="my_job",
    selection=AssetSelection.assets("get_my_data", "my_data_in_postgres"),
    tags={"audience": "internal", "domain": "ops", "pii": "false"},
)

my_job_schedule = ScheduleDefinition(name="my_job_schedule", job=my_job, cron_schedule="0 6 * * *")
```

### dbt job selection

```python
from dagster_dbt import build_dbt_asset_selection
from dagster_project.assets.transformations.dbt_assets import dbt_silver_stg, dbt_silver_core, dbt_gold_analytics

if dbt_silver_stg is not None:
    my_dbt_job = define_asset_job(
        name="my_dbt_job",
        selection=(build_dbt_asset_selection([dbt_silver_stg], dbt_select="tag:staging")
                 | build_dbt_asset_selection([dbt_silver_core], dbt_select="tag:core")
                 | build_dbt_asset_selection([dbt_gold_analytics], dbt_select="tag:analytics")),
    )
else:
    my_dbt_job = None   # None values filtered out in definitions.py
```

---

## SQL Queries

Store in `sql/ingestion.py` or `sql/exports.py`, import into assets:

```python
from dagster_project.sql.ingestion import CREATE_MY_TABLE, UPSERT_MY_RECORD

# For DataFrames, use: postgres_conn.query_to_polars(SELECT_MY_DATA)
```

## dbt Integration

dbt models are split by tag in `assets/transformations/dbt_assets.py`:

| dbt tag         | Dagster asset        | Layer          |
| --------------- | -------------------- | -------------- |
| `tag:staging`   | `dbt_silver_stg`     | Silver staging |
| `tag:core`      | `dbt_silver_core`    | Silver core    |
| `tag:analytics` | `dbt_gold_analytics` | Gold analytics |

Tags are auto-applied by `dbt_project.yml` based on directory. New dbt models appear in Dagster automatically. Config is in `dbt_config.py` which conditionally loads the project (returns `None` if dbt dir doesn't exist).

## Key file paths

| What                 | Path                                                                               |
| -------------------- | ---------------------------------------------------------------------------------- |
| Definitions          | `services/dagster/src/dagster_project/definitions.py`                              |
| Assets               | `services/dagster/src/dagster_project/assets/{ingestion,transformations,exports}/` |
| Resources (registry) | `services/dagster/src/dagster_project/resources/__init__.py`                       |
| Jobs                 | `services/dagster/src/dagster_project/jobs/`                                       |
| SQL queries          | `services/dagster/src/dagster_project/sql/`                                        |
| dbt config           | `services/dagster/src/dagster_project/dbt_config.py`                               |
| Slack hooks          | `services/dagster/src/dagster_project/ops/slack_hooks.py`                          |
