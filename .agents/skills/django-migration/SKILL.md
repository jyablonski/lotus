---
name: django-migration
description: >
  Step-by-step workflow for making Django model changes and creating/applying database
  migrations in the Lotus project. Use this skill whenever the user wants to add a field,
  create a new model, modify an existing model, add seed data, or run makemigrations/migrate
  commands. Also trigger for questions about the migration state, rolling back migrations,
  or anything touching services/django/core/models.py or services/django/core/migrations/.
---

# Django Migration Workflow

Django service: `services/django/`
Models: `services/django/core/models.py`
Migrations: `services/django/core/migrations/`
Docker service name: `django_admin`

---

## Step 1 — Edit the model

Open `services/django/core/models.py` and make the desired changes:

- New model: add a class inheriting from `models.Model`
- New field: add to an existing model class
- Modified field: change type, constraints, defaults, etc.

Read the file first to understand existing patterns (UUID PKs, `db_table`, `db_column` conventions) before making changes.

## Step 2 — Ensure the database is running

The `django_admin` container must be up and `postgres` must be healthy before running migrations.

If services aren't running:

```bash
make up
```

If you want to check without starting everything:

```bash
docker compose -f docker/docker-compose-local.yaml ps django_admin postgres
```

> The `django_admin` service has a volume mount (`services/django:/app`), so edits to local files are immediately reflected in the container — no rebuild needed.

## Step 3 — Generate the migration file

```bash
docker compose -f docker/docker-compose-local.yaml exec django_admin python manage.py makemigrations
```

This creates a new file in `services/django/core/migrations/` following the pattern `000N_description.py`.

After it runs, **read the generated file** and verify:

- The `dependencies` list chains correctly to the previous migration
- The operations match what you intended (correct field types, names, constraints)
- Nothing unexpected was detected (Django sometimes picks up unrelated drift)

To give the migration a descriptive name instead of auto-generated:

```bash
docker compose -f docker/docker-compose-local.yaml exec django_admin python manage.py makemigrations --name describe_your_change
```

## Step 4 — Apply the migration

```bash
docker compose -f docker/docker-compose-local.yaml exec django_admin python manage.py migrate
```

Watch for errors. Common issues:

- Column already exists → the DB is ahead of the migration history; check `showmigrations`
- Relation does not exist → dependency on a table that hasn't been created yet

## Step 5 — Verify

```bash
docker compose -f docker/docker-compose-local.yaml exec django_admin python manage.py showmigrations
```

All migrations should show `[X]`. If any show `[ ]`, run migrate again.

---

## Adding seed data in a migration

When a migration needs to insert data (not just schema changes), use `migrations.RunSQL()` with both forward and reverse SQL so rollbacks work:

```python
migrations.RunSQL(
    sql="INSERT INTO source.my_table (id, name) VALUES (gen_random_uuid(), 'example');",
    reverse_sql="DELETE FROM source.my_table WHERE name = 'example';",
),
```

The database `search_path` is set to `source,public`, so models map to the `source` schema. Use explicit `source.table_name` in raw SQL to be unambiguous.

---

## Rolling back a migration

To revert to a previous migration state, pass the target migration number:

```bash
docker compose -f docker/docker-compose-local.yaml exec django_admin python manage.py migrate core 000N
```

Where `000N` is the migration you want to end up at (not the one you're undoing). Django will run the `reverse` operations of all migrations after that point.

---

## Key rules

- **Never edit existing migration files.** Once a migration has been applied anywhere, treat it as immutable. If something needs fixing, create a new migration.
- Migration files chain via `dependencies` — the order matters and must be kept linear within the `core` app.
- The `entrypoint.sh` runs `migrate` automatically on container start, so the migration will also apply on the next `make up` / container restart.
