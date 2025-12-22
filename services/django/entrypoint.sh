#!/bin/bash
set -e

echo "Waiting for database to be ready..."
until python -c "import psycopg2; psycopg2.connect(host='${DB_HOST}', port=${DB_PORT}, user='${DB_USER}', password='${DB_PASSWORD}', dbname='${DB_NAME}')" 2>/dev/null; do
  echo "Database is unavailable - sleeping"
  sleep 1
done

echo "Database is ready!"

# Create migrations for Django's built-in apps (if needed)
echo "Creating migrations..."
python manage.py makemigrations --noinput || echo "No new migrations to create"

# Run migrations
# - Django's built-in apps (admin, auth, sessions, etc.): Tables will be created normally
# - Core app: Models are unmanaged (managed=False), so migrations just mark as applied without creating tables
echo "Running migrations..."
python manage.py migrate

# Admin user will be created via data migration (0002_create_admin_user.py)

echo "Starting Django server..."
exec "$@"
