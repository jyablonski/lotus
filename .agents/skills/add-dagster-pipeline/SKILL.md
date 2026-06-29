---
name: add-dagster-pipeline
description: Manual skill, do not invoke automatically. Use only when user explicitly runs add-dagster-pipeline by name. Step-by-step workflow for adding a new end-to-end Dagster + dbt data pipeline to the Lotus project, using daily_sales_job as the baseline. Covers the 6-task flow (generate/gate -> bronze load -> dbt source freshness -> source tests -> silver build -> gold build), the defs-folder autoloader, the ingestion code layout, resources, the create_job helper, and how dbt picks up the source by tag. Use whenever the user wants to add a new Dagster pipeline, asset, ingestion source, job, schedule, resource, or asks how the bronze->silver->gold pipeline is wired.
disable-model-invocation: true
user-invocable: true
---

# Dagster Pipeline Workflow

Build a new end-to-end pipeline the way `daily_sales_job` is built: ingest + gate data, land it in bronze Postgres, then let dbt run source freshness, bronze source tests, and the silver/gold builds selected by tag.

Source root: `services/dagster/src/dagster_project/` | dbt project: `services/dbt/`

## The baseline: `daily_sales_job` (the 6-task flow)

`defs/jobs/daily_sales_job.py` wires one job over six assets. Read it first — every new source pipeline is a copy of this shape.

| #   | Task (asset name)              | Where it's defined                               | What it does                                                                 |
| --- | ------------------------------ | ------------------------------------------------ | ---------------------------------------------------------------------------- |
| 1   | `sales_data`                   | `defs/assets/ingestion/get_sales_data.py`        | Fetch/generate the partition's rows, run in-memory **gates**, hold as Polars |
| 2   | `sales_data_bronze`            | `defs/assets/ingestion/get_sales_data.py`        | Write the gated frame to bronze Postgres (`source.sales_data`)               |
| 3   | `revenue_dbt_source_freshness` | `defs/assets/transformations/sales_dbt_tasks.py` | `dbt source freshness --select source:revenue`                               |
| 4   | `revenue_dbt_source_tests`     | `defs/assets/transformations/sales_dbt_tasks.py` | `dbt test --select source:revenue` (the bronze gate)                         |
| 5   | `revenue_dbt_silver_build`     | `defs/assets/transformations/sales_dbt_tasks.py` | `dbt build --select tag:silver,tag:revenue`                                  |
| 6   | `revenue_dbt_gold_build`       | `defs/assets/transformations/sales_dbt_tasks.py` | `dbt build --select tag:gold,tag:revenue`                                    |

Tasks 1–2 are hand-written Dagster assets (Python ingestion). Tasks 3–6 are produced by `build_dbt_source_pipeline()` and bound in the per-source dbt-tasks module. Dependencies chain `1 → 2 → 3 → 4 → 5 → 6`: freshness (3) waits on the bronze load (2), silver (5) gets an explicit dep on the source-tests gate (4), and gold (6) inherits it through dbt `ref()`.

```python
# defs/jobs/daily_sales_job.py
from dagster_project.defs.assets.ingestion.get_sales_data import (
    sales_data,
    sales_data_bronze,
)
from dagster_project.defs.assets.transformations.sales_dbt_tasks import sales_pipeline
from dagster_project.defs.jobs.utils import Audience, Domain, create_job

sales_pipeline_assets = [
    sales_data,
    sales_data_bronze,
    *(sales_pipeline.assets() if sales_pipeline else []),  # drops None dbt layers
]

daily_sales_job, daily_sales_schedule = create_job(
    name="daily_sales_job",
    assets=sales_pipeline_assets,
    audience=Audience.INTERNAL,
    domain=Domain.ANALYTICS,
    pii=False,
    schedule="0 12 * * *",  # 12:00 PM UTC daily
)
```

---

## How discovery works (read before adding files)

Everything under `defs/` is autoloaded. `definitions.py` calls `dg.load_from_defs_folder(...)` — there is **no** manual asset/job registry. Drop a module under `defs/` that binds a top-level asset/job/schedule/sensor and it is picked up. Two consequences:

- A factory that returns Dagster objects but defines none at module scope (e.g. `dbt_pipeline.py`, which lives **outside** `defs/` on purpose) is invisible until a module under `defs/` calls it and **binds the result to a module-level name**.
- `None` values are ignored by the loader, so the `... if sales_pipeline else None` guards are safe in unit tests where the dbt manifest isn't mounted.

| Component | Autoloaded? | How to add                                                                       |
| --------- | ----------- | -------------------------------------------------------------------------------- |
| Assets    | Yes         | Bind an `@asset` at module scope under `defs/assets/...`                         |
| Jobs      | Yes         | Bind a job under `defs/jobs/...` (use `create_job`)                              |
| Schedules | Yes         | Return it from `create_job(schedule=...)` alongside the job                      |
| Sensors   | Yes         | Bind under `defs/sensors/`                                                       |
| Resources | **No**      | Register in `resources/__init__.py` `RESOURCES`; surfaced by `defs/resources.py` |

---

## Step-by-step: add a new source pipeline

Mirror the revenue/sales pipeline. Replace `revenue`/`sales`/`my_*` throughout.

### Step 1 — Ingestion asset (generate + gate)

`defs/assets/ingestion/get_my_data.py`. Return a `pl.DataFrame` held in memory so the bronze loader is a separate, retryable step. Gate with helpers from `dagster_project.gates` (`check_min_rows`, `check_for_nulls`, which raise `GateError`). Use the partition + metadata helpers in `defs/assets/ingestion/utils.py`.

```python
from dagster import AssetExecutionContext, DailyPartitionsDefinition, asset
import polars as pl

from dagster_project.defs.assets.ingestion.utils import (
    create_basic_metadata, get_partition_date,
)
from dagster_project.gates import check_for_nulls, check_min_rows

daily_partitions = DailyPartitionsDefinition(start_date="2025-12-18")

@asset(group_name="ingestion", partitions_def=daily_partitions)
def my_data(context: AssetExecutionContext) -> pl.DataFrame:
    """Fetch and gate the partition's rows, held in memory for the bronze load."""
    partition_date = get_partition_date(context)
    df = pl.DataFrame(...)  # fetch from API / generate

    row_count = check_min_rows(df)     # raises GateError below floor
    check_for_nulls(df, column="id")   # raises GateError on nulls

    context.add_output_metadata(create_basic_metadata(context, num_rows=row_count, df=df))
    return df
```

### Step 2 — Bronze load asset

Same file, second asset. Depend on Step 1 by parameter name; inject `postgres_conn: PostgresResource`. Write with `write_to_postgres(...)` into the `source` schema (bronze) with `conflict_columns` for idempotent upserts.

```python
from dagster_project.resources import PostgresResource

MY_TABLE_NAME = "my_data"

@asset(group_name="ingestion", partitions_def=daily_partitions)
def my_data_bronze(
    context: AssetExecutionContext,
    my_data: pl.DataFrame,             # dependency by parameter name
    postgres_conn: PostgresResource,    # resource injection by RESOURCES key
) -> None:
    """Load the gated partition into bronze Postgres."""
    written = postgres_conn.write_to_postgres(
        df=my_data, table_name=MY_TABLE_NAME, schema="source", conflict_columns=["id"],
    )
    context.add_output_metadata(create_basic_metadata(context, num_rows=written, df=my_data))
```

### Step 3 — dbt source + models (in `services/dbt/`)

This is what makes tasks 3–6 do anything. See `add-dbt-model` for full detail. The conventions the Dagster side relies on:

- **Source** (`models/sources/<source>/<source>.yml`): a `sources:` entry whose `schema: source` and table name match what Step 2 wrote. Column `data_tests` (e.g. `unique`, `not_null`) are the **bronze source tests** run by task 4. Add a `loaded_at_field` + `freshness:` block for task 3 to enforce.
- **Layer tag** comes from the directory via `dbt_project.yml` (`models/silver/staging → [silver, staging]`, `core → [silver, core]`, `models/gold/analytics → [gold, analytics]`).
- **Data-source tag** is added per model in its `.yml` `config.tags: ["<source>"]`.

So `stg_my_data` ends up tagged `silver, staging, <source>`, the core model `silver, core, <source>`, and the gold model `gold, analytics, <source>`. The per-source pipeline selects on the `tag:<layer>,tag:<source>` pairs.

### Step 4 — Per-source dbt tasks module

`defs/assets/transformations/my_dbt_tasks.py`. Call the factory and **bind every step at module scope** so the autoloader registers them.

```python
from dagster_project.dbt_pipeline import build_dbt_source_pipeline
from dagster_project.defs.assets.ingestion.get_my_data import my_data_bronze

MY_SOURCE_NAME = "my_source"  # must equal the dbt source name AND the per-model tag

my_pipeline = build_dbt_source_pipeline(
    data_source=MY_SOURCE_NAME,
    bronze_asset=my_data_bronze,   # task 3 freshness waits on this ingestion asset
)

# None when the dbt manifest isn't mounted (unit tests) or a layer has no matching
# tagged model. The defs-folder autoloader ignores None.
my_dbt_source_freshness = my_pipeline.source_freshness if my_pipeline else None
my_dbt_source_tests = my_pipeline.source_tests if my_pipeline else None
my_dbt_silver_build = my_pipeline.silver_build if my_pipeline else None
my_dbt_gold_build = my_pipeline.gold_build if my_pipeline else None
```

**Register the new source for exclusion.** `dbt_pipeline.py` has `SOURCE_PIPELINE_DATA_SOURCES` — add your source there. The whole-warehouse layered `dbt_assets.py` excludes these tags so each dbt model belongs to exactly one `@dbt_assets` definition (otherwise Dagster raises "Duplicate asset key").

### Step 5 — The job

`defs/jobs/my_job.py`. Copy `daily_sales_job.py`: list the two ingestion assets, splat `my_pipeline.assets()`, and call `create_job` with the standard tag enums.

```python
from dagster_project.defs.assets.ingestion.get_my_data import my_data, my_data_bronze
from dagster_project.defs.assets.transformations.my_dbt_tasks import my_pipeline
from dagster_project.defs.jobs.utils import Audience, Domain, create_job

my_pipeline_assets = [my_data, my_data_bronze, *(my_pipeline.assets() if my_pipeline else [])]

my_job, my_schedule = create_job(
    name="my_job",
    assets=my_pipeline_assets,
    audience=Audience.INTERNAL,   # INTERNAL | USER_FACING
    domain=Domain.ANALYTICS,      # ANALYTICS | FEATURE_STORE | GAME | INGESTION | OPS
    pii=False,
    schedule="0 12 * * *",        # omit to return just the job
)
```

`create_job` (`defs/jobs/utils.py`) applies the standard `audience`/`domain`/`pii` tags via `standard_tags()`, builds the `define_asset_job`, and — when `schedule=` is passed — also returns a paired `ScheduleDefinition`. Pass **either** `assets=` (list of asset defs/keys) **or** `selection=` (a prebuilt `AssetSelection`), never both.

### Step 6 — Verify

```bash
cd services/dagster
uv run pytest                              # unit + integration tests
uv run dagster definitions validate        # asset graph loads, no duplicate keys
```

Add a unit test under `tests/unit/assets/ingestion/` for the gates and bronze write (mock `PostgresResource`), mirroring `test_get_sales_data.py`.

---

## Two ways dbt models become Dagster assets

**1. Per-source pipeline** (this skill) — `build_dbt_source_pipeline()` in `dagster_project/dbt_pipeline.py`. One chain per bronze source:

```
source freshness (source:<src>) → source tests (source:<src>)
    → silver build (tag:silver,tag:<src>) → gold build (tag:gold,tag:<src>)
```

Freshness/tests are plain `@asset` ops (dbt sources have no model node to materialize), run with `dbt.cli([...]).wait()` so they fail fast. Silver/gold are real `@dbt_assets` so their models appear in the graph; they run with `.stream()`. `silver_build`/`gold_build` are `None` when no model carries the `tag:<layer>,tag:<src>` pair. `SourceTestsGateTranslator` injects the silver→source-tests dep.

**2. Whole-warehouse layered** (`defs/assets/transformations/dbt_assets.py`) — one `@dbt_assets` per layer tag for everything _not_ owned by a per-source pipeline: `dbt_silver_stg` (`tag:staging`), `dbt_silver_core` (`tag:core`), `dbt_gold_analytics` (`tag:analytics`), with `exclude=source_pipeline_exclude()`. Jobs select across these with `dbt_tag_selection([...], tag="game")` (see `game_bets_pipeline_job.py`) and pass it as `selection=` to `create_job`.

---

## Adding a resource (not autoloaded)

1. Create `resources/my_resource.py` with a `ConfigurableResource` subclass and a module-level instance bound to `EnvVar(...)`.
2. Register in `resources/__init__.py`: add to `__all__` and the `RESOURCES` dict. The dict key **is** the asset parameter name used for injection. `defs/resources.py` wraps `RESOURCES` (plus the `dbt` `DbtCliResource`) into the `Definitions` the autoloader picks up.
3. Add env vars to the dagster service in `docker/docker-compose-local.yaml`.

```python
# resources/my_resource.py
from dagster import ConfigurableResource, EnvVar

class MyResource(ConfigurableResource):
    api_key: str
    def get_client(self): ...

my_resource = MyResource(api_key=EnvVar("MY_RESOURCE_API_KEY"))
```

---

## Key file paths

| What                        | Path                                                                    |
| --------------------------- | ----------------------------------------------------------------------- |
| Definitions (autoloader)    | `src/dagster_project/definitions.py`                                    |
| Ingestion assets            | `src/dagster_project/defs/assets/ingestion/`                            |
| Gate helpers                | `src/dagster_project/gates.py`                                          |
| Ingestion utils (metadata)  | `src/dagster_project/defs/assets/ingestion/utils.py`                    |
| Per-source dbt tasks        | `src/dagster_project/defs/assets/transformations/<source>_dbt_tasks.py` |
| dbt source-pipeline factory | `src/dagster_project/dbt_pipeline.py`                                   |
| Layered dbt assets          | `src/dagster_project/defs/assets/transformations/dbt_assets.py`         |
| dbt project/manifest config | `src/dagster_project/dbt_config.py`                                     |
| Jobs                        | `src/dagster_project/defs/jobs/`                                        |
| `create_job` / tag enums    | `src/dagster_project/defs/jobs/utils.py`                                |
| Resource registry           | `src/dagster_project/resources/__init__.py` + `defs/resources.py`       |
| SQL queries                 | `src/dagster_project/sql/`                                              |
| dbt models / sources        | `services/dbt/models/{sources,silver,gold}/`                            |
