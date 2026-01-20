#!/bin/bash

# Bufet Web Server Startup Script for Linux

# Exit on error
set -e

echo "Starting Bufet Web Server..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install dependencies if needed
echo "Installing dependencies..."
pip install -r requirements.txt

# Apply database migrations
echo "Applying migrations..."
python manage.py migrate

# Create superuser if needed (interactive)
# python manage.py createsuperuser

# Start the development server
echo "Starting Django development server..."
python manage.py runserver 0.0.0.0:8000

# For production with Gunicorn, uncomment below and ensure gunicorn is in requirements.txt:
# echo "Starting server with Gunicorn..."
# gunicorn bufet_project.wsgi:application --bind 0.0.0.0:8000
