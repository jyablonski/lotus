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

## Admin Access Control

The `AdminOnlyMiddleware` restricts access to users with the `Admin` role:

1. User must be authenticated
2. User must exist in the `users` table (by email match)
3. User must have `role = 'Admin'`

## Testing

### Running Tests

```bash
# Run all tests with coverage
uv run pytest
```

### Test Considerations for `managed=False` Models

The core models use `managed=False` because their tables are created externally (via `docker/db/01-bootstrap.sql`). This creates testing challenges:

**Problem:** Django won't create tables for unmanaged models in the test database.

**Solution:** The `conftest.py` fixture `setup_test_database` handles this by:

1. Creating the `source` schema and `uuid-ossp` extension
2. Using Django's `SchemaEditor` to manually create tables for all unmanaged models
3. Sorting models by FK dependencies to ensure parent tables are created first

```python
# From conftest.py - creates tables for unmanaged models
with connection.schema_editor() as schema_editor:
    for model in unmanaged_models:
        schema_editor.create_model(model)
```

**Migration Considerations:** The `0002_create_admin_user` migration queries the `users` table. It includes a `table_exists()` check to skip gracefully during tests when the table doesn't exist yet.

### Test Fixtures

| Fixture               | Description                                                               |
| --------------------- | ------------------------------------------------------------------------- |
| `setup_test_database` | Creates schema and tables for unmanaged models (session-scoped, auto-use) |
| `admin_user`          | Creates Django user + LotusUser with Admin role                           |
| `admin_client`        | Authenticated test client with admin user                                 |

## Database Configuration

- **Engine:** PostgreSQL
- **Schema:** `source` (set via `search_path` in settings)
- **Tables:** Most exist externally; `feature_flags` is Django-managed

## Notes

- Use `--fake-initial` for migrations since most tables already exist
- The `FeatureFlag` model is the only fully managed model
- Admin authentication bridges Django's auth system with the Lotus `users` table
