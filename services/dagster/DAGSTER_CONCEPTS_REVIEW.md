# Dagster Concepts Review

## Currently Implemented ✅

Your `definitions.py` currently includes:

1. **Assets** ✅ - Using `load_assets_from_package_module(assets)`
2. **Asset Checks** ✅ - Using `load_asset_checks_from_package_module(assets)`
3. **Jobs** ✅ - Auto-discovered from `jobs` module
4. **Schedules** ✅ - Auto-discovered from `jobs` module
5. **Resources** ✅ - Auto-discovered from `resources` module

## Missing from Definitions API

Based on the [Definitions API docs](https://docs.dagster.io/api/dagster/definitions), here are important concepts you're not using yet:

### 1. **Sensors** 🔴 Missing

**What:** Event-driven triggers that monitor external systems and trigger jobs
**Why:** Better than schedules for file-based ingestion, API polling, or event-driven pipelines
**Use Cases:**

- Watch S3 bucket for new files
- Monitor database for new records
- Trigger on webhook events
- Poll external APIs

**Example:**

```python
# sensors/file_watcher.py
from dagster import sensor, SensorEvaluationContext, RunRequest
from dagster_project.jobs import daily_sales_job

@sensor(job=daily_sales_job)
def s3_file_sensor(context: SensorEvaluationContext):
    # Check S3 for new files
    new_files = check_s3_for_new_files()
    if new_files:
        return RunRequest(run_key=f"file-{new_files[0]}")
    return SkipReason("No new files found")
```

### 2. **Partitions** 🔴 Missing

**What:** Logical divisions of data (time-based, categorical) for incremental processing
**Why:** Essential for large datasets, backfills, and incremental processing
**Use Cases:**

- Daily/hourly data processing
- Region-based partitioning
- Backfilling historical data
- Incremental updates

**Example:**

```python
from dagster import DailyPartitionsDefinition, asset

daily_partitions = DailyPartitionsDefinition(start_date="2024-01-01")

@asset(partitions_def=daily_partitions)
def sales_data_partitioned(context: AssetExecutionContext) -> pl.DataFrame:
    partition_date = context.partition_key
    # Process only data for this partition
    return fetch_sales_for_date(partition_date)
```

### 3. **Source Assets** 🟡 Partially Missing

**What:** External data sources not produced by Dagster
**Why:** Track external dependencies, enable lineage, document data sources
**Use Cases:**

- External databases
- Third-party APIs
- Files in S3/GCS
- Existing tables

**Example:**

```python
from dagster import SourceAsset, AssetKey

external_sales_db = SourceAsset(
    key=AssetKey(["postgres", "source", "sales"]),
    description="External sales database table",
    metadata={"database": "postgres", "schema": "source", "table": "sales"}
)
```

### 4. **Metadata** 🟡 Underutilized

**What:** Rich metadata for observability and documentation
**Why:** Better UI visibility, documentation, monitoring
**Use Cases:**

- Row counts, data quality metrics
- Schema information
- Owner/team information
- Links to documentation

**Example:**

```python
from dagster import MetadataValue

@asset
def sales_data(context: AssetExecutionContext) -> pl.DataFrame:
    df = generate_sales_data()

    context.add_output_metadata({
        "num_rows": MetadataValue.int(len(df)),
        "schema": MetadataValue.json(df.schema),
        "owner": MetadataValue.text("data-team"),
        "docs": MetadataValue.url("https://docs.example.com/sales")
    })
    return df
```

### 5. **Ops** 🟢 Intentionally Skipped (Good!)

**What:** Side-effect operations without data artifacts
**Why:** You're using assets-first approach, which is recommended
**Note:** Only use ops if you need side effects without data outputs (notifications, cleanup, etc.)

## Recommended Additions

### Priority 1: Partitions

**Why:** Your `daily_sales_job` would benefit from daily partitions for:

- Backfilling historical data
- Reprocessing specific days
- Incremental processing
- Better observability per partition

### Priority 2: Sensors

**Why:** If you have file-based ingestion or need event-driven triggers, sensors are more efficient than polling schedules

### Priority 3: Metadata

**Why:** Improve observability and documentation in the Dagster UI

### Priority 4: Source Assets

**Why:** If you have external data sources, document them as source assets

## Implementation Suggestions

### 1. Add Partitions to Daily Sales Job

```python
# jobs/daily_sales_job.py
from dagster import (
    AssetSelection,
    DailyPartitionsDefinition,
    ScheduleDefinition,
    define_asset_job,
)

daily_partitions = DailyPartitionsDefinition(start_date="2024-01-01")

daily_sales_job = define_asset_job(
    name="daily_sales_job",
    selection=AssetSelection.assets("sales_data", "sales_summary"),
    partitions_def=daily_partitions,  # Add partitions
)

daily_sales_schedule = ScheduleDefinition(
    name="daily_sales_schedule",
    job=daily_sales_job,
    cron_schedule="0 1,13 * * *",
)
```

### 2. Add Sensors Module

```python
# sensors/__init__.py
from .file_watcher import s3_file_sensor

__all__ = ["s3_file_sensor"]
```

### 3. Update definitions.py

```python
# definitions.py additions
from dagster import (
    # ... existing imports
    load_sensors_from_package_module,
)

from dagster_project import (
    assets,
    jobs,
    resources as resources_module,
    sensors,  # Add sensors module
)

# In definitions.py
defs = Definitions(
    assets=load_assets_from_package_module(assets),
    asset_checks=load_asset_checks_from_package_module(assets),
    jobs=all_jobs,
    schedules=all_schedules,
    sensors=load_sensors_from_package_module(sensors),  # Add sensors
    resources=all_resources,
)
```

### 4. Add Metadata to Assets

```python
@asset(group_name="ingestion")
def sales_data(context: AssetExecutionContext) -> pl.DataFrame:
    df = generate_sales_data()

    context.add_output_metadata({
        "num_rows": MetadataValue.int(len(df)),
        "date_range": MetadataValue.text(f"{df['date'].min()} to {df['date'].max()}"),
    })
    return df
```

## Summary

You have a solid foundation with assets, checks, jobs, schedules, and resources. The most impactful additions would be:

1. **Partitions** - Essential for production data pipelines
2. **Sensors** - If you need event-driven triggers
3. **Metadata** - Improves observability
4. **Source Assets** - If you have external dependencies

Your current architecture is clean and follows best practices. These additions would enhance it further for production use.
