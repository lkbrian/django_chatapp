#!/bin/bash
echo "Making migrations"
python3 manage.py makemigrations
echo "======making....======"

echo "Migrated"
python3 manage.py migrate
echo "======migrating....======"

echo "Starting Daphne (ASGI) server"
daphne -b 0.0.0.0 -p 8000 chatapp.asgi:application
