#!/bin/bash
set -e

echo "Starting Bufet Web Server..."

PROJECT_DIR="$HOME/Desktop/bufet"
VENV_DIR="$PROJECT_DIR/venv"

cd "$PROJECT_DIR"

# Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Confirm correct python & pip
which python
which pip

echo "Updating code from GitHub..."

BRANCH="main"
export GIT_TERMINAL_PROMPT=0

git fetch origin --prune
git reset --hard origin/$BRANCH
git clean -fd

echo "Git update complete."

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Running migrations..."
python manage.py migrate --noinput

echo "Starting Django server..."
python manage.py runserver_plus 0.0.0.0:8000 --cert-file localhost+2.pem --key-file localhost+2-key.pem
