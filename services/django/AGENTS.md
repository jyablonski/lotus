# Django Admin Service - Agent Guide

Django application for database migrations, admin interface, and internal data management.

## Technology Stack

- **Framework**: Django 5.0+
- **Language**: Python 3.13
- **Database**: PostgreSQL
- **Admin UI**: django-unfold (modern admin theme)
- **Dependency Management**: uv (pyproject.toml)

## Architecture Patterns

### Purpose

The Django service serves two main purposes:

1. **Database Migrations** - Manages database schema changes
2. **Admin Interface** - Internal admin UI for managing application data and feature flags

### Model Organization

- Models are in `core/models.py`
- Each model represents a database table
- Models use Django ORM for database access

### Admin Interface

- Admin classes are in `core/admin.py`
- Uses `django-unfold` for modern UI
- Custom admin actions and filters are defined per model

## Code Organization

```
core/
├── models.py              # Django models (database tables)
├── admin.py              # Admin interface configuration
├── management/           # Custom management commands
│   └── commands/
├── middleware.py         # Custom middleware (AdminOnlyMiddleware)
├── signals.py            # Django signals (post_save, etc.)
├── backends.py           # Custom authentication backends
└── migrations/           # Database migrations (auto-generated)

lotus_admin/
├── settings.py           # Django settings
├── urls.py               # URL routing
├── wsgi.py               # WSGI configuration
└── asgi.py               # ASGI configuration
```

## Key Patterns

### Database Migrations

- Migrations are auto-generated from model changes
- **Never edit migration files manually** (except for data migrations)
- Create migrations: `python manage.py makemigrations`
- Apply migrations: `python manage.py migrate`

### Model Definition

```python
class ModelName(models.Model):
    field = models.FieldType(...)

    class Meta:
        db_table = 'table_name'
        # ... other Meta options
```

### Admin Registration

```python
@admin.register(ModelName)
class ModelNameAdmin(admin.ModelAdmin):
    list_display = ['field1', 'field2']
    list_filter = ['field1']
    search_fields = ['field2']
```

### Signals

- Use signals for side effects (e.g., calling Analyzer service)
- Signals are in `core/signals.py`
- Common signals: `post_save`, `pre_save`, `post_delete`

## Testing

### Test Structure

- Tests are in `tests/` directory
- Use `pytest` with `pytest-django`
- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Test Markers

- `@pytest.mark.unit` - Unit tests (no external dependencies)
- `@pytest.mark.integration` - Integration tests (require database)
- `@pytest.mark.django_db` - Django database tests

### Running Tests

```bash
# From service directory
pytest

# With coverage
pytest --cov=core --cov-report=term-missing

# Run specific test
pytest tests/test_models.py::TestUserModel
```

### Test Database

- Tests use a separate test database
- Database is created/destroyed automatically
- Use `@pytest.mark.django_db` decorator for database access

## Configuration

### Environment Variables

- `DJANGO_SECRET_KEY` - Secret key for Django (required in production)
- `DJANGO_DEBUG` - Debug mode (default: `True` in dev)
- `DJANGO_ALLOWED_HOSTS` - Allowed hostnames (comma-separated)
- `DB_NAME` - Database name (default: `postgres`)
- `DB_USER` - Database user (default: `postgres`)
- `DB_PASSWORD` - Database password (default: `postgres`)
- `DB_HOST` - Database host (default: `postgres`)
- `DB_PORT` - Database port (default: `5432`)
- `ANALYZER_BASE_URL` - Analyzer service URL for signals

### Settings

- Settings are in `lotus_admin/settings.py`
- Use environment variables for configuration
- Debug mode is enabled by default in development

## Key Files to Understand

Before making changes:

1. **`core/models.py`** - Database models
2. **`core/admin.py`** - Admin interface configuration
3. **`core/signals.py`** - Django signals (side effects)
4. **`core/middleware.py`** - Custom middleware
5. **`lotus_admin/settings.py`** - Django configuration
6. **`lotus_admin/urls.py`** - URL routing

## Common Tasks

### Adding a New Model

1. Define model in `core/models.py`
2. Create migration: `python manage.py makemigrations`
3. Apply migration: `python manage.py migrate`
4. Register model in admin: `core/admin.py`
5. Write tests: `tests/test_models.py`

### Creating a Migration

```bash
# Create migration from model changes
python manage.py makemigrations

# Create empty migration (for data migrations)
python manage.py makemigrations --empty core

# Apply migrations
python manage.py migrate
```

### Adding Admin Functionality

1. Register model in `core/admin.py`
2. Customize `list_display`, `list_filter`, `search_fields`
3. Add custom admin actions if needed
4. Test in admin interface

### Creating Management Commands

1. Create file: `core/management/commands/command_name.py`
2. Define `Command` class inheriting from `BaseCommand`
3. Implement `handle()` method
4. Run: `python manage.py command_name`

### Adding Signals

1. Define signal handler in `core/signals.py`
2. Connect signal in `core/apps.py` or `core/__init__.py`
3. Use `@receiver` decorator for cleaner code
4. Test signal behavior

## Code Style

- Follow root `pyproject.toml` Ruff configuration
- Use Django conventions for model field names
- Use type hints where helpful
- Keep models focused and normalized
- Use signals sparingly (prefer explicit method calls when possible)

## Database Schema Management

### Migration Workflow

1. **Modify models** in `core/models.py`
2. **Create migration**: `python manage.py makemigrations`
3. **Review migration** file in `core/migrations/`
4. **Test migration**: `python manage.py migrate` (on test DB)
5. **Commit** both model changes and migration files

### Data Migrations

- Use `RunPython` for data migrations
- Always make migrations reversible (`reverse_code` parameter)
- Test data migrations on copy of production data

### Schema Changes

- Schema changes affect the Go backend (sqlc queries)
- Coordinate schema changes with backend team
- Update sqlc queries after Django migrations

## Security

### Admin Access

- `AdminOnlyMiddleware` restricts admin interface to admin users
- Only superusers can access admin interface
- Regular users cannot access admin even if authenticated

### Secret Key

- **Never commit** `DJANGO_SECRET_KEY` to version control
- Use strong, random secret key in production
- Rotate secret key periodically

### Debug Mode

- **Never enable** `DJANGO_DEBUG=True` in production
- Debug mode exposes sensitive information
- Use environment variable to control debug mode

## Integration with Other Services

### Analyzer Service

- Signals call Analyzer service via HTTP
- `ANALYZER_BASE_URL` environment variable configures endpoint
- Used for triggering ML analysis after model changes

### Backend Service

- Shares same PostgreSQL database
- Backend uses sqlc-generated queries (must match Django models)
- Coordinate schema changes between Django and backend

## Pre-commit Hooks

- Ruff linting and formatting (inherited from root)
- Django-specific checks may be added

## Deployment

- Uses `Dockerfile` for containerization
- Port: 8000
- Health check: Admin login page
- Database migrations run automatically on startup (via entrypoint.sh)
