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

## Admin Access Control

The `AdminOnlyMiddleware` restricts access to the admin interface. Users can access if they meet any of the following:

1. **Admin Role**: User must be authenticated, exist in the `users` table (by email match), and have `role = 'Admin'`
2. **Allowed Groups**: User must be in one of the Django groups specified in `ADMIN_ALLOWED_GROUPS` (default: `product_manager`, `ml_engineer`)
