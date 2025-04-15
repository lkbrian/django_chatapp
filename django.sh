#!/bin/bash
echo "Making migrations"
python3 manage.py makemigrations
echo "======making....======"

echo "Migrated"
python3 manage.py migrate
echo "======migrating....======"

echo "starting server"
python3 manage.py runserver 0.0.0:8000
echo "======serving started....======"