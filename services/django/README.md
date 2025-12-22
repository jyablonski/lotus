# Lotus Django Admin

Internal-only Django admin interface for managing Lotus data.

## Setup

### 1. Install Dependencies

### 3. Handle Migrations

Since the database tables already exist from `docker/db/01-bootstrap.sql`, you need to:

1. Create migrations for Django's built-in apps (admin, auth, sessions, etc.):

   ```bash
   python manage.py makemigrations
   ```

2. Mark migrations as applied (fake) since tables already exist:

   ```bash
   python manage.py migrate --fake-initial
   ```

   Or use the convenience command:

   ```bash
   python manage.py fake_migrations
   ```

**Note:** The core app models are unmanaged (`managed = False`), so `makemigrations core` will show "No changes detected" - this is expected. Django won't create migrations for unmanaged models.

### 4. Create Admin User

To access the admin interface, you need to create a Django admin user linked to a Lotus user with Admin role.

First, ensure you have a user in the `users` table with `role = 'Admin'`. Then create the Django admin user:

```bash
python manage.py create_admin_user --email your-admin@example.com --password your-password
```

### 5. Run Development Server

```bash
python manage.py runserver
```

Access the admin interface at: http://localhost:8000/admin/

## Admin Access Control

The admin interface is restricted to users with the `Admin` role in the `users` table. The middleware checks:

1. User is authenticated
2. User exists in the `users` table
3. User has `role = 'Admin'`

## Project Structure

- `lotus_admin/` - Django project settings and configuration
- `core/` - Main app with models and admin interface
  - `models.py` - Database models (unmanaged, matching existing schema)
  - `admin.py` - Admin interface configuration
  - `middleware.py` - Admin-only access middleware
  - `backends.py` - Custom authentication backend
  - `management/commands/` - Custom management commands

## Models

All models are set to `managed = False` since the tables already exist:

- `User` - Users table
- `Journal` - Journal entries
- `JournalDetail` - Journal analysis details
- `JournalTopic` - ML topics for journals
- `JournalSentiment` - Sentiment analysis for journals

## Notes

- The database uses PostgreSQL with the `source` schema
- Models are unmanaged - Django won't create/modify tables
- Use `--fake-initial` for migrations since tables exist
- Admin authentication uses the existing `users` table
