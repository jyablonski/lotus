---
name: dbt-model
description: >
  Step-by-step workflow for adding new dbt models to the Lotus analytics project.
  Covers source definitions, the silver/gold medallion architecture (staging stg_,
  core fct_/dim_, gold analytics), incremental materialization, tagging, primary key
  tests, and dbt-utils tests. Use this skill whenever the user wants to add a new
  dbt model, source, or test, or asks how the dbt layer structure works.
---

# dbt Model Workflow

dbt project: `services/dbt/` | Packages: `services/dbt/packages.yml` (includes `dbt-utils`)

## Architecture: Medallion Layers

```
Source (external tables in source schema)
  -> Silver / Staging  (stg_*)        light transforms, rename columns
  -> Silver / Core     (fct_*, dim_*) business logic, joins, derived fields
  -> Gold / Analytics  (marts)        aggregated, business-ready tables
```

Output schemas (`silver` or `gold`) are controlled by `dbt_project.yml` + `macros/generate_schema_name.sql`. Tagging (`staging`, `core`, `analytics`) and grouping are auto-applied by directory.

---

## Step 1: Define the source

**Location:** `models/sources/application_db/{table_name}.yml` -- one file per table, all use `schema: source` and `name: application_db`.

```yaml
version: 2
sources:
  - name: application_db
    schema: source
    tables:
      - name: my_table
        description: Description of the table
        columns:
          - name: id
          - name: user_id
          - name: created_at
          - name: modified_at
```

## Step 2: Staging model (Silver / Staging)

Light transforms: rename columns, cast types. Always incremental on `modified_at` with a default value of `1970-01-01` for the initial load.

**SQL:** `models/silver/staging/stg_{table_name}.sql`

```sql
{{ config(materialized='incremental', unique_key='{primary_key}') }}

with source as (
    select * from {{ source('application_db', 'my_table') }}
    {% if is_incremental() %}
    where modified_at > coalesce((select max(modified_at) from {{ this }}), '1970-01-01'::timestamp)
    {% endif %}
),
renamed as (
    select
        id as my_id,
        user_id,
        name as my_name,
        created_at,
        modified_at
    from source
)
select * from renamed
```

**YAML:** `models/silver/staging/stg_{table_name}.yml` -- primary key always gets `unique` + `not_null`:

```yaml
version: 2
models:
  - name: stg_my_table
    columns:
      - name: my_id
        data_tests: [unique, not_null]
      - name: user_id
        data_tests: [not_null]
      - name: created_at
        data_tests: [not_null]
```

## Step 3: Core models (Silver / Core)

Reference staging via `{{ ref('stg_...') }}`, never `{{ source() }}`. Two types:

### Dimension tables (dim\_\*) -- `materialized='table'`

```sql
{{ config(materialized='table') }}
with source as (select * from {{ ref('stg_my_table') }}),
final as (
    select my_id, my_name, created_at as my_created_at from source
)
select * from final
```

### Fact tables (fct\_\*) -- `materialized='incremental'` with derived fields

```sql
{{ config(materialized='incremental', unique_key='{primary_key}') }}

with events as (
    select * from {{ ref('stg_events') }}
    {% if is_incremental() %}
    where created_at > coalesce((select max(event_created_at) from {{ this }}), '1970-01-01'::timestamp)
    {% endif %}
),
final as (
    select
        event_id, user_id, event_type,
        case when event_type = 'purchase' then amount else 0 end as purchase_amount,
        amount > 0 as is_positive,
        created_at as event_created_at
    from events
)
select * from final
```

**YAML** -- add `accepted_values` for enums, domain-level `config.tags`:

```yaml
version: 2
models:
  - name: fct_my_events
    config:
      tags: ["my_domain"]
    columns:
      - name: event_id
        data_tests: [unique, not_null]
      - name: event_type
        data_tests:
          - not_null
          - accepted_values:
              arguments:
                values: ["purchase", "refund", "view"]
```

## Step 4: Gold analytics (Gold / Analytics)

Heavily aggregated, `materialized='table'`. Multi-CTE pattern with time windows, safe division.

```sql
{{ config(materialized='table') }}

with facts as (select * from {{ ref('fct_my_events') }}),
users as (select * from {{ ref('dim_users') }}),
user_metrics as (
    select user_id, count(*) as total_events, sum(purchase_amount) as total_amount
    from facts group by user_id
),
user_metrics_30d as (
    select user_id, count(*) as total_events_30d
    from facts
    where date_trunc('day', event_created_at)::date >= current_date - interval '29 days'
    group by user_id
),
final as (
    select
        users.user_id, users.user_email,
        coalesce(m.total_events, 0) as total_events,
        coalesce(m30.total_events_30d, 0) as total_events_30d
    from users
    left join user_metrics m on users.user_id = m.user_id
    left join user_metrics_30d m30 on users.user_id = m30.user_id
)
select * from final
```

**YAML** -- `relationships` for FK tests, `dbt_utils.expression_is_true` for range checks:

```yaml
version: 2
models:
  - name: my_summary
    config:
      tags: ["my_domain"]
    columns:
      - name: user_id
        data_tests:
          - unique
          - not_null
          - relationships:
              arguments: { to: "ref('dim_users')", field: user_id }
      - name: total_events
        data_tests:
          - not_null
          - dbt_utils.expression_is_true:
              arguments: { expression: ">= 0" }
```

---

## Test patterns reference

| Test                           | Usage                                 | Layer      |
| ------------------------------ | ------------------------------------- | ---------- |
| `unique` + `not_null`          | Primary key (required on every model) | All        |
| `not_null`                     | Required columns                      | All        |
| `accepted_values`              | Enum validation                       | Core, Gold |
| `relationships`                | Foreign key to dim/ref table          | Core, Gold |
| `dbt_utils.expression_is_true` | Numeric ranges, cross-column checks   | Gold       |

Use `config.where` to scope tests: e.g., `where: "win_rate is not null"` or `where: "total_bets > 0"`.

## Dagster integration

dbt models are auto-picked up by Dagster via tags (`tag:staging` / `tag:core` / `tag:analytics`). Place your model in the correct directory and it appears in Dagster automatically -- no Dagster code changes needed.

## Key file paths

| What            | Path                                                          |
| --------------- | ------------------------------------------------------------- |
| Project config  | `services/dbt/dbt_project.yml`                                |
| Sources         | `services/dbt/models/sources/application_db/{table}.yml`      |
| Staging         | `services/dbt/models/silver/staging/stg_{table}.sql` + `.yml` |
| Core (fact/dim) | `services/dbt/models/silver/core/fct_{domain}.sql` + `.yml`   |
| Gold analytics  | `services/dbt/models/gold/analytics/{summary}.sql` + `.yml`   |
| Schema macro    | `services/dbt/macros/generate_schema_name.sql`                |
| Groups          | `services/dbt/models/_groups.yml`                             |
