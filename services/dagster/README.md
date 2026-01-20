# Dagster Project

This Dagster project orchestrates data pipelines with automatic discovery of assets, jobs, and resources.

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

The `definitions.py` file automatically discovers and loads assets, jobs, schedules, and resources from their respective modules.

### Assets

Assets are automatically discovered from the `assets` package using `load_assets_from_package_module()`. Any Python file containing `@asset` decorators within the `assets/` directory structure will be automatically included.

**Example:**

```python
# assets/ingestion/get_api_assets.py
@asset(group_name="ingestion")
def api_users(context: AssetExecutionContext) -> list[dict]:
    """Fetch users from API."""
    # ...
```

### Jobs and Schedules

Jobs and schedules are auto-discovered from the `jobs` module. The `definitions.py` file scans all objects in the `jobs` module and includes:

- `JobDefinition` instances
- `UnresolvedAssetJobDefinition` instances
- `ScheduleDefinition` instances

**To add a new job:**

1. Create a job file in `jobs/` (e.g., `jobs/my_job.py`)
2. Import it in `jobs/__init__.py`
3. It will automatically be available in the Dagster UI

**Example:**

```python
# jobs/game_types_job.py
from dagster import define_asset_job, AssetSelection

get_game_types_job = define_asset_job(
    name="get_game_types_job",
    selection=AssetSelection.assets("get_game_types_from_api"),
)
```

### Resources

Resources are auto-discovered from the `resources` module. The `load_resources()` function scans all `ConfigurableResource` and `ResourceDefinition` instances and adds them to the resources dictionary.

**To add a new resource:**

1. Create a resource file in `resources/` (e.g., `resources/my_resource.py`)
2. Define a `ConfigurableResource` subclass or `ResourceDefinition` instance
3. Import it in `resources/__init__.py`
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

## dbt Integration

The project integrates with a dbt project located at `../dbt` (relative to `src/dagster_project/`). The integration is configured in `dbt_config.py`.

### Loading dbt Assets

dbt models are loaded as Dagster assets via the `dbt_analytics` asset in `assets/transformations/dbt_assets.py`. This asset uses the dbt manifest file to discover all dbt models and expose them as Dagster assets.

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
   Retrieves features from Redis by entity ID for low-latency inference. The API calls this to fetch precomputed features without hitting Postgres.

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

| File                 | Purpose                                                                                                        |
| -------------------- | -------------------------------------------------------------------------------------------------------------- |
| `feature_store.yaml` | Configures PostgreSQL as the registry (metadata storage), Postgres as the offline store (source of truth), and Redis as the online store (low-latency serving) |
| `entities.py`        | Defines entities like `user_entity` which serve as join keys for feature lookups                               |
| `feature_views.py`   | Defines feature views that map SQL queries to typed feature schemas                                            |

### Resources

| Resource        | Location             | Purpose                                                                    |
| --------------- | -------------------- | -------------------------------------------------------------------------- |
| `FeastResource` | `resources/feast.py` | Dagster resource that provides a configured Feast `FeatureStore` instance  |
| `RedisResource` | `resources/redis.py` | Dagster resource for direct Redis access (used for verification/debugging) |
