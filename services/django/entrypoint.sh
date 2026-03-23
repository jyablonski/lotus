#!/bin/bash
set -e

echo "Waiting for database to be ready..."
until python -c "import psycopg2; psycopg2.connect(host='${DB_HOST}', port=${DB_PORT}, user='${DB_USER}', password='${DB_PASSWORD}', dbname='${DB_NAME}')" 2>/dev/null; do
  echo "Database is unavailable - sleeping"
  sleep 1
done

echo "Database is ready!"

# Check for missing migrations (developers should create these before committing)
echo "Checking for missing migrations..."
if ! python manage.py makemigrations --check --dry-run > /dev/null 2>&1; then
    echo "ERROR: Missing migrations detected!"
    echo "Run 'python manage.py makemigrations' locally and commit the migration files."
    exit 1
fi
echo "All migrations are up to date."

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Admin user will be created via data migration (0002_create_admin_user.py)

echo "Starting Django server..."
exec "$@"
