#!/bin/sh

echo "Waiting for postgres..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

echo "Collecting static files"
python manage.py collectstatic --no-input

# Start the Gunicorn server
echo "Starting Gunicorn server..."
exec gunicorn wa_router.wsgi:application --bind 0.0.0.0:8000
