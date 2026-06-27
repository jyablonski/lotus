# Dagster

Dagster is an orchestration tool primarily used for scheduling data pipelines.

Jobs consist of a collection of assets (for data pipelines) or ops (for non-data tasks) that are executed in a specific order.

- Assets are Dagster's core concept for data pipelines and are defined using the `@asset` decorator. Data quality checks can be defined on assets and stored as metadata during job execution.
- Ops are Dagster's core concept for non-data tasks and are defined using the `@op` decorator.
- Assets and ops can be sequenced together to form pipelines.

## Dagster Components

Tilt wires Dagster as three Compose resources, all using the same `dagster_server_image`.

- `dagster_base`: gRPC code server on port 4000; it loads `dagster_project.definitions`, and `workspace.yaml` points the other Dagster services at it.
- `dagster_webserver`: UI/API service on host port 3001; it reads `workspace.yaml`, stores metadata in Postgres, and talks to `dagster_base`.
- `dagster_daemon`: background scheduler/queue worker that starts scheduled or queued runs; there is no separate local worker service.
- Dockerfile stages: `base` sets Python/OS env, `deps` installs the locked uv environment, and `runtime` copies `.venv`, dbt, Feast, Dagster config, and `src`.
- Tilt builds `dagster-base` from the `deps` stage for dependency caching, then builds the runtime image as `dagster_server_image`; `docker-compose-tilt.yaml` disables Compose builds so Tilt owns rebuilds.
- Local dev uses `DefaultRunLauncher`, so new Dagster runs execute from the running Dagster service image, not a fresh Docker task. If `DockerRunLauncher` is enabled later, those run containers are configured to use `dagster_server_image`.
- Demo/example assets and jobs are excluded from the default code location; set `DAGSTER_INCLUDE_EXAMPLES=true` to load them.

## Directory Structure

```
src/dagster_project/
├── assets/              # Data assets organized by purpose
│   ├── ingestion/      # Assets that fetch data from external sources (APIs, etc.)
│   ├── transformations/# Assets that transform data (including dbt models)
│   ├── exports/        # Assets that export data to external systems (S3, etc.)
│   └── internal/       # Internal processing assets
├── jobs/               # Job and schedule definitions
├── resources/          # Reusable resources (database connections, API clients, etc.)
├── dbt_config.py       # Configuration for dbt project integration
└── definitions.py      # Main entry point that auto-loads all components
```

## Auto-Loading Mechanism

The `definitions.py` file walks the Dagster packages, loads assets/jobs/schedules/sensors, and combines them with the explicit resource registry.

### Assets

Assets are discovered by walking importable modules under `assets/` and passing those modules to `load_assets_from_modules()`. Demo/example asset modules are skipped unless `DAGSTER_INCLUDE_EXAMPLES=true`.

**Example:**

```python
# assets/ingestion/get_api_assets.py
@asset(group_name="ingestion")
def api_users(context: AssetExecutionContext) -> list[dict]:
    """Fetch users from API."""
    # ...
```

### Jobs and Schedules

Jobs and schedules are discovered by walking importable modules under `jobs/`. The `definitions.py` file scans each loaded module and includes:

- `JobDefinition` instances
- `UnresolvedAssetJobDefinition` instances
- `ScheduleDefinition` instances

**To add a new job:**

1. Create a job file in `jobs/` (e.g., `jobs/my_job.py`)
2. Import the asset definitions the job should select
3. It will automatically be available in the Dagster UI

**Example:**

```python
# jobs/game_types_job.py
from dagster_project.assets.ingestion.get_game_types_from_api import get_game_types_from_api
from dagster_project.jobs.utils import Audience, Domain, create_job

get_game_types_job = create_job(
    name="get_game_types_job",
    assets=[get_game_types_from_api],
    audience=Audience.INTERNAL,
    domain=Domain.GAME,
    pii=False,
)
```

### Resources

Resources are explicitly registered in `resources.RESOURCES`. Assets refer to resources by key, so every new resource used by an asset must be added to that registry.

Examples of Resources:

- `PostgresResource` - for connecting to a PostgreSQL database
- `RedisResource` - for connecting to a Redis instance
- `GoogleSheetsResource` - for connecting to a Google Sheets instance

To create a resource, 2 things must be created:

- A `ConfigurableResource` subclass for the resource (ex: `PostgresResource`)
- A `ResourceDefinition` instance for the resource (ex: `postgres_conn`) which gets pulled in and used by assets

**To add a new resource:**

1. Create a resource file in `resources/` (e.g., `resources/my_resource.py`)
2. Define a `ConfigurableResource` subclass or `ResourceDefinition` instance
3. Import it in `resources/__init__.py` and add it to `RESOURCES`
4. It will automatically be available for use in assets

**Example:**

```python
# resources/postgres.py
from dagster import ConfigurableResource

class PostgresResource(ConfigurableResource):
    host: str = "postgres"
    # ... other config fields

postgres_conn = PostgresResource(...)
```

Then in the asset code, the resource can be used like this:

```python
@asset
def my_asset(context: AssetExecutionContext, postgres_conn: PostgresResource) -> None:
    with postgres_conn.get_connection() as conn:
        conn.execute("SELECT * FROM my_table")
```

## dbt Integration

The project integrates with a dbt project located at `../dbt` (relative to `src/dagster_project/`). The integration is configured in `dbt_config.py`, which conditionally loads the project from its manifest (returns `None` if the dbt dir/manifest isn't available, e.g. in unit tests).

### Loading dbt Assets

There are two conventions for turning dbt models into Dagster assets.

**1. Layered tags (whole warehouse).** `assets/transformations/dbt_assets.py` splits every model by layer tag into one asset per layer, so each layer runs as its own step:

| dbt tag         | Dagster asset        | Layer          |
| --------------- | -------------------- | -------------- |
| `tag:staging`   | `dbt_silver_stg`     | Silver staging |
| `tag:core`      | `dbt_silver_core`    | Silver core    |
| `tag:analytics` | `dbt_gold_analytics` | Gold analytics |

**2. Per-source pipeline (bronze → silver → gold).** A single data source flows through a standard four-step chain, built by `build_dbt_source_pipeline()` from `dagster_project.dbt_pipeline`:

| Step             | dbt command                                          |
| ---------------- | ---------------------------------------------------- |
| source freshness | `dbt source freshness --select source:<data_source>` |
| source tests     | `dbt test --select source:<data_source>`             |
| silver build     | `dbt build --select tag:silver,tag:<data_source>`    |
| gold build       | `dbt build --select tag:gold,tag:<data_source>`      |

```python
# assets/transformations/sales_dbt_tasks.py
from dagster_project.dbt_pipeline import build_dbt_source_pipeline
from dagster_project.defs.assets.ingestion.get_sales_data import sales_data_bronze

sales_pipeline = build_dbt_source_pipeline(
    data_source="sales_data",
    bronze_asset=sales_data_bronze,  # freshness waits on this ingestion asset
)

# Bind each step at module scope so the autoloader registers it.
sales_data_dbt_source_freshness = sales_pipeline.source_freshness if sales_pipeline else None
sales_data_dbt_source_tests = sales_pipeline.source_tests if sales_pipeline else None
sales_data_dbt_silver_build = sales_pipeline.silver_build if sales_pipeline else None
sales_data_dbt_gold_build = sales_pipeline.gold_build if sales_pipeline else None
```

Notes:

- The factory lives at `dagster_project/dbt_pipeline.py`, **outside** `assets/`, because it defines no top-level Dagster objects and must not be scanned by the autoloader. The autoloader only registers top-level `AssetsDefinition` objects, so each per-source module **must** bind the returned steps to module-scope names (as above).
- Silver assets get an explicit dependency on the source-tests gate (via `SourceTestsGateTranslator`); gold inherits it transitively because gold models `ref()` silver.
- `silver_build` / `gold_build` are `None` when no model carries the matching `tag:<layer>,tag:<data_source>` pair, so an empty dbt selection never raises.
- Adding a new source pipeline is one `build_dbt_source_pipeline(...)` call plus the four module-scope bindings.

### Manifest Regeneration

**Important:** The dbt manifest (`manifest.json`) must be manually regenerated whenever you make changes to your dbt project (add/remove models, change configurations, etc.) for Dagster to pick up those changes.

To regenerate the manifest:

```bash
cd services/dbt
dbt compile --profiles-dir ./profiles --profile local
```

Or if you're using `uv`:

```bash
cd services/dbt
uv run dbt compile --profiles-dir ./profiles --profile local
```

The manifest is generated in `services/dbt/target/manifest.json` and is automatically used by Dagster when loading dbt assets.

**Note:** If dbt assets don't appear in the Dagster UI after making changes to your dbt project, regenerate the manifest using the command above.

## Feast

This project uses [Feast](https://feast.dev/) to serve precomputed features for low-latency online inference. Feast reads aggregated data from the PostgreSQL `gold` schema and materializes it to Redis for fast retrieval by the Analyzer API Service.

### How It Works

Feast operates in three distinct phases:

1. **Apply** (`feast apply` or `store.apply()`)
   Registers feature definitions (entities, feature views, source queries) to the registry. This is metadata only—no data moves. Think of it like a database migration that tells Feast "these features exist."

2. **Materialize** (`store.materialize()`)
   Executes the source SQL query against Postgres, reads the rows, and writes them to Redis keyed by entity ID. This is the actual data sync that populates the online store.

3. **Serve** (`store.get_online_features()`)
   Retrieves features from Redis by entity ID for low-latency inference. The Analyzer API Service calls this to fetch precomputed features from Redis w/ low latency, without having to get them from Postgres which would be slower.

The Dagster asset `materialize_user_journal_features` handles steps 1-2: it applies definitions if missing, then materializes data to Redis on a schedule.

### Architecture

```
┌─────────────────┐    materialize    ┌─────────────┐    get_online_features    ┌──────────────────────┐
│  PostgreSQL     │ ───────────────►  │    Redis    │  ◄─────────────────────── │   Analyzer Service   │
│  (gold schema)  │                   │   (online)  │                           │                      │
└─────────────────┘                   └─────────────┘                           └──────────────────────┘
        │
   dbt models
   transform data
```

### Directory Structure

```
feast_repo/
├── feature_store.yaml   # Feast configuration (registry, offline/online store connections)
├── entities.py          # Entity definitions (e.g., user_entity with join key user_id)
└── feature_views.py     # Feature view definitions (SQL sources, schemas, TTL)
```

**Note:** The Feast registry is stored in PostgreSQL (configured in `feature_store.yaml`), not in a local file. This enables concurrent access and better scalability.

### Key Files

| File                 | Purpose                                                                                                                                                        |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `feature_store.yaml` | Configures PostgreSQL as the registry (metadata storage), Postgres as the offline store (source of truth), and Redis as the online store (low-latency serving) |
| `entities.py`        | Defines entities like `user_entity` which serve as join keys for feature lookups                                                                               |
| `feature_views.py`   | Defines feature views that map SQL queries to typed feature schemas                                                                                            |

### Resources

| Resource        | Location             | Purpose                                                                    |
| --------------- | -------------------- | -------------------------------------------------------------------------- |
| `FeastResource` | `resources/feast.py` | Dagster resource that provides a configured Feast `FeatureStore` instance  |
| `RedisResource` | `resources/redis.py` | Dagster resource for direct Redis access (used for verification/debugging) |
