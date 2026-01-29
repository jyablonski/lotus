# Dagster Service - Agent Guide

Dagster orchestration service for managing data pipelines, dbt runs, and scheduled workflows.

## Technology Stack

- **Framework**: Dagster 1.12.6
- **Language**: Python 3.13
- **Database**: PostgreSQL (for Dagster metadata)
- **Integrations**: dbt, Feast, Redis
- **Dependency Management**: uv (pyproject.toml)

## Architecture Patterns

### Service Components

Dagster runs as **three separate services**:

1. **dagster_base** - gRPC server for code location
2. **dagster_webserver** - Web UI for monitoring and running jobs
3. **dagster_daemon** - Background daemon for scheduled runs

All three services use the same Docker image but different entrypoints.

### Code Location Pattern

- Code location is defined in `workspace.yaml`
- Uses `dagster_project` as the root module
- Assets, ops, and jobs are organized in `src/dagster_project/`

### Asset-Based Architecture

Dagster uses **assets** as the primary abstraction:

- Assets represent data products (tables, files, etc.)
- Assets have dependencies (upstream assets)
- Assets can be materialized (computed/updated)
- Materialization creates a run that executes ops

## Code Organization

```
src/
├── dagster_project/
│   ├── __init__.py           # Code location definition
│   ├── assets/               # Asset definitions
│   │   ├── analytics.py      # Analytics assets
│   │   └── dbt.py            # dbt assets
│   ├── jobs/                 # Job definitions
│   │   └── analytics.py      # Scheduled jobs
│   ├── ops/                  # Operation definitions
│   │   └── dbt.py           # dbt operations
│   ├── resources/            # Resource definitions
│   │   ├── dbt_resource.py   # dbt resource
│   │   └── postgres.py      # PostgreSQL resource
│   └── schedules/            # Schedule definitions
│       └── analytics.py     # Scheduled runs

workspace.yaml                # Workspace configuration
```

## Key Patterns

### Asset Definition

```python
@asset(
    group_name="analytics",
    compute_kind="dbt",
    deps=[upstream_asset],
)
def asset_name(context: AssetExecutionContext) -> MaterializeResult:
    # Asset computation logic
    return MaterializeResult(metadata={...})
```

### Resource Definition

```python
@resource(config_schema={...})
def resource_name(context: InitResourceContext):
    # Resource initialization
    return ResourceObject(...)
```

### Job Definition

```python
@job(
    config={"ops": {...}},
    resource_defs={"dbt": dbt_resource},
)
def job_name():
    # Define asset materialization
    materialize([asset1, asset2])
```

### Schedule Definition

```python
@schedule(
    job=job_name,
    cron_schedule="0 0 * * *",  # Daily at midnight
)
def schedule_name(context: ScheduleEvaluationContext):
    return RunRequest(run_key=..., tags={...})
```

## Testing

### Test Structure

- Tests are in `tests/` directory
- Use `pytest` with Dagster test utilities
- Test files: `test_*.py`

### Test Markers

- `@pytest.mark.unit` - Unit tests (no external dependencies)
- `@pytest.mark.integration` - Integration tests (require services)
- `@pytest.mark.slow` - Slow-running tests

### Running Tests

```bash
# From service directory
pytest

# With coverage
pytest --cov=dagster_project --cov-report=term

# Run specific test
pytest tests/test_assets.py
```

### Testing Assets

- Use `materialize` function to test asset materialization
- Mock resources for unit tests
- Use real resources for integration tests

## Configuration

### Environment Variables

- `DAGSTER_POSTGRES_USER` - PostgreSQL user for Dagster metadata
- `DAGSTER_POSTGRES_PASSWORD` - PostgreSQL password
- `DAGSTER_POSTGRES_HOST` - PostgreSQL host
- `DAGSTER_POSTGRES_PORT` - PostgreSQL port
- `DAGSTER_POSTGRES_DB` - PostgreSQL database name
- `DAGSTER_HOME` - Dagster home directory (default: `/opt/dagster/dagster_home`)
- `DBT_PROFILES_DIR` - dbt profiles directory (default: `/app/dbt/profiles`)
- `REDIS_HOST` - Redis host for caching
- `REDIS_PORT` - Redis port
- `REDIS_DB` - Redis database number
- `API_KEY` - API key for external services
- `SLACK_WEBHOOK_URL` - Slack webhook for notifications
- `SLACK_BOT_TOKEN` - Slack bot token
- `SLACK_DEFAULT_CHANNEL` - Default Slack channel
- `FEATURE_FLAGS_GOOGLE_SHEET_URL` - Feature flags Google Sheet URL
- `FEATURE_FLAGS_GOOGLE_SHEET_CREDENTIALS_JSON` - Google Sheet credentials

### Workspace Configuration

- `workspace.yaml` defines code locations and loadable targets
- Points to `dagster_project` module
- Loads assets, jobs, schedules from the module

## Key Files to Understand

Before making changes:

1. **`workspace.yaml`** - Workspace configuration
2. **`src/dagster_project/__init__.py`** - Code location definition
3. **`src/dagster_project/assets/`** - Asset definitions
4. **`src/dagster_project/jobs/`** - Job definitions
5. **`src/dagster_project/resources/`** - Resource definitions
6. **`src/dagster_project/schedules/`** - Schedule definitions

## Common Tasks

### Adding a New Asset

1. Define asset in `src/dagster_project/assets/`
2. Specify dependencies (upstream assets)
3. Implement computation logic
4. Add to appropriate job
5. Test asset materialization

### Creating a Job

1. Define job in `src/dagster_project/jobs/`
2. Specify assets to materialize
3. Configure resources
4. Register job in code location
5. Test job execution

### Adding a Schedule

1. Define schedule in `src/dagster_project/schedules/`
2. Associate with a job
3. Set cron schedule
4. Register schedule in code location
5. Verify schedule appears in UI

### Integrating dbt

1. Use `dagster-dbt` integration
2. Define dbt resource in `src/dagster_project/resources/dbt_resource.py`
3. Create dbt assets using `load_assets_from_dbt_project()`
4. Configure dbt profiles directory
5. Test dbt runs via Dagster

### Adding Resources

1. Define resource in `src/dagster_project/resources/`
2. Specify config schema
3. Implement initialization logic
4. Use resource in assets/ops
5. Configure resource in jobs

## Code Style

- Follow root `pyproject.toml` Ruff configuration
- Use type hints for all functions
- Use Dagster's type system for asset outputs
- Keep assets focused and single-purpose
- Use meaningful asset and op names

## Integration with dbt

### dbt Assets

- dbt models are loaded as Dagster assets
- Use `load_assets_from_dbt_project()` to create assets from dbt
- dbt runs are executed via Dagster ops
- dbt profiles are configured via `DBT_PROFILES_DIR`

### dbt Resource

- dbt resource provides dbt CLI interface
- Configured with dbt project path and profiles directory
- Used by dbt ops to execute dbt commands

## Integration with Feast

- Feast is configured for feature store
- `FEAST_REPO_PATH` environment variable points to Feast repository
- Feast resources can be used in assets/ops

## Monitoring & Observability

### Run Monitoring

- View runs in Dagster UI
- Check run logs for errors
- Monitor run duration and status
- Set up alerts for failed runs

### Slack Notifications

- Configure `SLACK_WEBHOOK_URL` for notifications
- Dagster can send run status updates to Slack
- Use `SLACK_DEFAULT_CHANNEL` for default channel

## Pre-commit Hooks

- Ruff linting and formatting (inherited from root)
- Service-specific import sorting configured

## Deployment

- Uses single `Dockerfile` for all three services
- Different entrypoints for base, webserver, and daemon
- Ports: 4000 (base gRPC), 3001 (webserver HTTP)
- Health checks configured for base service
- Volumes mounted for code and dbt project

## Best Practices

1. **Asset Naming**: Use descriptive names that indicate data product
2. **Dependencies**: Explicitly define asset dependencies
3. **Resources**: Share resources across assets when possible
4. **Error Handling**: Handle errors gracefully in assets/ops
5. **Testing**: Test assets in isolation before integrating
6. **Documentation**: Document asset purpose and dependencies
7. **Scheduling**: Use appropriate cron schedules for jobs
8. **Monitoring**: Monitor run success rates and durations
