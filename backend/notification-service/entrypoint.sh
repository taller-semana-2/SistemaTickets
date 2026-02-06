#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Starting notification consumer in background..."
# Ejecuta el consumidor como módulo para que Python resuelva paquetes correctamente
python -m notifications.messaging.consumer &

echo "Starting Django development server..."
exec python manage.py runserver 0.0.0.0:8000
