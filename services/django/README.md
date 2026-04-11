# Lotus Django Admin

Django App to serve as a schema migration tool as well as an Admin web interface for managing various things related to the project.

After running the app, access the admin interface at: http://localhost:8000/admin/

## Directory Structure

```
services/django/
├── core/                   # Main application
│   ├── admin.py            # Admin interface configuration
│   ├── backends.py         # Custom authentication backend (Lotus users)
│   ├── middleware.py       # Admin-only access middleware
│   ├── models.py           # Database models (managed=False for existing tables)
│   ├── urls.py             # URL routing
│   └── management/
│       └── commands/       # Custom management commands
│           ├── create_admin_user.py
│           └── fake_migrations.py
├── lotus_admin/            # Django project configuration
│   ├── settings.py         # Project settings
│   ├── urls.py             # Root URL configuration
│   └── wsgi.py             # WSGI application
├── tests/                  # Test suite
│   ├── conftest.py         # Pytest fixtures and test database setup
│   ├── test_admin.py       # Admin interface tests
│   ├── test_backends.py    # Authentication backend tests
│   ├── test_middleware.py  # Middleware tests
│   └── test_models.py      # Model tests
├── manage.py               # Django CLI
├── pyproject.toml          # Dependencies and pytest config
└── Dockerfile              # Container build
```

## Quick Start

```bash
# Start all services (from repo root)
make up

# Teardown
make down
```

The `entrypoint.sh` script manages Django's startup:

1. Checks for missing migrations (fails if model changes aren't committed)
2. Runs existing migrations
3. Starts the Django server

### Creating Migrations

If you modify models, create migrations locally before committing:

1. Make model changes in `core/models.py`
2. Generate migration files:
   ```bash
   cd services/django
   uv run python manage.py makemigrations
   ```
3. Commit the new migration file from `core/migrations/`

The entrypoint will reject startup if migrations are missing.

#### Command Cheat Sheet

```py
uv run python manage.py makemigrations # generate new migration files
uv run python manage.py migrate core 0006_remove_featureflag # rollback to specific migration
uv run python manage.py migrate # run migrations
uv run python manage.py generate_example_journal_data # create 100 users + 10000 journals via backend + analyzer flow
```

Example:

```bash
uv run python manage.py generate_example_journal_data --users 10 --journals 1000 --reset-prefix
```

`generate_example_journal_data` creates journals through `POST /v1/journals`, so keep the backend running at `BACKEND_BASE_URL` (defaults to `http://localhost:8080`) and set `BACKEND_API_KEY` so the command can send `Authorization: Bearer ...`.

## Admin Access Control

The `AdminOnlyMiddleware` restricts access to the admin interface. Users can access if they meet any of the following:

1. **Admin Role**: User must be authenticated, exist in the `users` table (by email match), and have `role = 'Admin'`
2. **Allowed Groups**: User must be in one of the Django groups specified in `ADMIN_ALLOWED_GROUPS`:
   - `product` - Product team members
   - `ml_ops` - ML Operations team members
   - `infrastructure` - Infrastructure team members
   - `engineering` - Engineering team members

## Stakeholder-Controlled Toggles

One useful pattern is giving non-technical teammates access to a very small part of the system so they can safely flip functionality on or off without needing code changes or a full deploy.

In this repo, `product` and `ml_ops` group members can manage the `ActiveMLModel` admin screen, which writes to the `active_ml_models` table. That makes the Django admin a lightweight control panel for turning specific model-backed behavior on or off.

This is a good fit for:

- Enabling or disabling a specific ML model version
- Giving product or ML stakeholders a safe way to test rollout decisions
- Letting internal teams control operational switches without broader admin ownership

The same general approach also works for other "flip the bit" surfaces such as feature flags, runtime config, or model-backed booleans:

1. Store the toggle in the database
2. Register the model in Django admin
3. Restrict access with group-based admin permissions
4. Seed or assign the relevant Django groups for the stakeholders who should control it

### Example Test Users

Migration [`0022_seed_ml_model_admin_test_users.py`](./core/migrations/0022_seed_ml_model_admin_test_users.py) creates two example stakeholder accounts you can use locally:

- `product-test@lotus.dev` in the `product` group
- `mlops-test@lotus.dev` in the `ml_ops` group

Both use the password `testpass123`.
