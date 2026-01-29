# dbt Service - Agent Guide

dbt (data build tool) for transforming and modeling data in the analytics layer.

## Technology Stack

- **Tool**: dbt-core 1.10.13+
- **Adapter**: dbt-postgres 1.9.1+
- **Language**: SQL (with Jinja templating)
- **Dependency Management**: uv (pyproject.toml)

## Architecture Patterns

### dbt Project Structure

dbt follows a **layered architecture** (staging → silver → gold):

1. **Staging** (`models/silver/staging/`) - Raw data transformations
2. **Silver** (`models/silver/core/`) - Cleaned, validated data models
3. **Gold** (`models/gold/`) - Final analytics-ready models

### Model Organization

- **Sources** (`models/sources/`) - Source table definitions
- **Staging** - Initial transformations from sources
- **Silver** - Business logic and core models
- **Gold** - Final aggregated/analytics models

### Naming Conventions

- Staging models: `stg_{source_table_name}`
- Silver models: `dim_{dimension_name}` or `fct_{fact_name}`
- Gold models: Descriptive names for analytics

## Code Organization

```
models/
├── sources/                    # Source table definitions
│   └── application_db/
│       ├── journals.yml
│       ├── users.yml
│       └── ...
├── silver/
│   ├── staging/               # Staging layer models
│   │   ├── stg_journals.sql
│   │   ├── stg_users.sql
│   │   └── ...
│   └── core/                  # Silver layer models
│       ├── dim_users.sql
│       ├── fct_journal_entries.sql
│       └── ...
└── gold/                      # Gold layer models
    └── ...

macros/                         # Reusable SQL macros
├── .gitkeep
└── (custom macros)

profiles/                       # dbt profiles (local)
profiles.yml                    # dbt profiles configuration

dbt_project.yml                 # dbt project configuration
```

## Key Patterns

### Source Definition

```yaml
# models/sources/application_db/journals.yml
sources:
  - name: application_db
    tables:
      - name: journals
        columns:
          - name: id
            description: "Journal entry ID"
```

### Staging Model

```sql
-- models/silver/staging/stg_journals.sql
{{ config(materialized='view') }}

select
    id,
    user_id,
    title,
    content,
    created_at
from {{ source('application_db', 'journals') }}
```

### Silver Model (Dimension)

```sql
-- models/silver/core/dim_users.sql
{{ config(materialized='table') }}

select
    user_id,
    email,
    created_at as user_created_at
from {{ ref('stg_users') }}
```

### Silver Model (Fact)

```sql
-- models/silver/core/fct_journal_entries.sql
{{ config(materialized='table') }}

select
    stg_journals.id as journal_id,
    stg_journals.user_id,
    stg_journals.title,
    stg_journals.content,
    stg_journals.created_at,
    dim_users.email as user_email
from {{ ref('stg_journals') }}
left join {{ ref('dim_users') }}
    on stg_journals.user_id = dim_users.user_id
```

### Model Configuration

```yaml
# models/silver/core/dim_users.yml
version: 2

models:
  - name: dim_users
    description: "User dimension table"
    columns:
      - name: user_id
        description: "Unique user identifier"
        tests:
          - unique
          - not_null
```

## Testing

### dbt Tests

dbt provides built-in testing:

- **Generic tests**: `unique`, `not_null`, `accepted_values`, `relationships`
- **Singular tests**: Custom SQL tests
- **Schema tests**: Defined in `.yml` files

### Running Tests

```bash
# Run all tests
dbt test

# Run tests for specific model
dbt test --select dim_users

# Run tests for specific tag
dbt test --select tag:gold
```

### Test Definition

```yaml
# In model .yml file
models:
  - name: dim_users
    columns:
      - name: user_id
        tests:
          - unique
          - not_null
      - name: email
        tests:
          - unique
```

## Configuration

### dbt_project.yml

Main configuration file:

- Project name and version
- Profile name
- Model paths and configurations
- Macro paths
- Test paths

### Profiles Configuration

- `profiles.yml` - Local profiles (not committed)
- `profiles/profiles.yml` - Project profiles
- Configured with PostgreSQL connection details

### Environment Variables

- Database connection via dbt profiles
- Profiles directory: `DBT_PROFILES_DIR` (set by Dagster)

## Key Files to Understand

Before making changes:

1. **`dbt_project.yml`** - Project configuration
2. **`profiles/profiles.yml`** - Database connection configuration
3. **`models/sources/`** - Source table definitions
4. **`models/silver/staging/`** - Staging models
5. **`models/silver/core/`** - Core silver models
6. **`models/gold/`** - Gold/analytics models
7. **`macros/`** - Reusable SQL macros

## Common Tasks

### Adding a New Source Table

1. Define source in `models/sources/application_db/{table}.yml`
2. Document columns and descriptions
3. Reference source in staging models: `{{ source('application_db', 'table') }}`

### Creating a Staging Model

1. Create SQL file: `models/silver/staging/stg_{table}.sql`
2. Select from source: `{{ source('application_db', 'table') }}`
3. Apply basic transformations (renaming, type casting)
4. Add model config: `{{ config(materialized='view') }}`
5. Create YAML file for documentation: `stg_{table}.yml`

### Creating a Silver Model

1. Create SQL file: `models/silver/core/{model_type}_{name}.sql`
2. Reference staging models: `{{ ref('stg_table') }}`
3. Apply business logic and transformations
4. Add model config: `{{ config(materialized='table') }}`
5. Create YAML file with tests and documentation

### Adding Tests

1. Define tests in model `.yml` file
2. Use generic tests (`unique`, `not_null`, etc.)
3. Create singular tests for custom logic
4. Run tests: `dbt test --select {model_name}`

### Creating Macros

1. Create macro file in `macros/`
2. Define macro with Jinja syntax
3. Use macro in models: `{{ macro_name(arg1, arg2) }}`

## Code Style

### SQL Style

- Use consistent indentation (2 or 4 spaces)
- Use CTEs for complex queries
- **Do not use table aliases** - Use full table/model names for clarity and consistency
- Comment complex logic
- Follow SQL best practices

### Jinja Style

- Use Jinja for dynamic SQL generation
- Keep Jinja logic simple and readable
- Use `{{ ref() }}` for model references
- Use `{{ source() }}` for source references
- Use `{{ config() }}` for model configuration

### Naming Conventions

- Staging: `stg_{source_table}`
- Dimensions: `dim_{dimension_name}`
- Facts: `fct_{fact_name}`
- Gold: Descriptive names

## Integration with Dagster

### dbt Assets in Dagster

- dbt models are loaded as Dagster assets
- Dagster orchestrates dbt runs
- dbt runs are tracked in Dagster UI
- Use `dagster-dbt` integration

### Running dbt via Dagster

1. Configure dbt resource in Dagster
2. Create dbt assets from dbt project
3. Materialize assets via Dagster jobs
4. Monitor runs in Dagster UI

## Documentation

### Generating Documentation

```bash
# Generate docs
dbt docs generate

# Serve docs locally
dbt docs serve
```

### Documenting Models

- Add descriptions in `.yml` files
- Document columns with descriptions
- Add tests to validate data quality
- Use `dbt docs` to view lineage graphs

## Materialization Strategies

- **View**: Lightweight, always up-to-date (staging models)
- **Table**: Materialized, faster queries (core models)
- **Incremental**: Only process new data (large tables)
- **Ephemeral**: CTE, not materialized (intermediate models)

## Best Practices

1. **Layering**: Follow staging → silver → gold pattern
2. **Testing**: Test all models, especially core models
3. **Documentation**: Document all models and columns
4. **Naming**: Use consistent naming conventions
5. **Refs**: Always use `{{ ref() }}` for model dependencies
6. **Sources**: Always use `{{ source() }}` for source tables
7. **No Table Aliases**: Do not use table aliases (e.g., `j`, `u`) - use full model names for clarity
8. **Incremental**: Use incremental models for large tables
9. **Macros**: Create macros for reusable logic

## Pre-commit Hooks

- No specific dbt hooks (SQL linting may be added)
- Follow general SQL formatting guidelines

## Deployment

- dbt runs are executed via Dagster
- Dagster handles dbt project deployment
- Models are materialized in PostgreSQL
- Tests run as part of Dagster jobs
