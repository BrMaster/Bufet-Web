#!/bin/bash
set -e

echo "Starting Bufet Web Server..."

cd "$(dirname "$0")"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Updating code from GitHub..."

BRANCH="main"

# Prevent git from hanging forever
export GIT_TERMINAL_PROMPT=0

git fetch origin --prune
git reset --hard origin/$BRANCH
git clean -fd

echo "Git update complete."

pip install --upgrade pip
pip install -r requirements.txt

python manage.py migrate --noinput

echo "Starting Django server..."
python manage.py runserver 0.0.0.0:8000
