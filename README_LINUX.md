# Linux Startup Command for Bufet Web Server

## Quick Start

### Using the Startup Script (Recommended)

```bash
chmod +x start.sh
./start.sh
```

This script will:
1. Activate the virtual environment
2. Install dependencies
3. Apply database migrations
4. Start the Django development server on `0.0.0.0:8000`

## Manual Startup

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply migrations
python manage.py migrate

# 4. Create superuser (optional, first time only)
python manage.py createsuperuser

# 5. Start development server
python manage.py runserver 0.0.0.0:8000
```

The application will be available at: `http://localhost:8000/`
Admin panel: `http://localhost:8000/admin/`

## Production Deployment with Gunicorn

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn bufet_project.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

For systemd service, create `/etc/systemd/system/bufet.service`:

```ini
[Unit]
Description=Bufet Web Django Application
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/Bufet Web
ExecStart=/path/to/Bufet Web/venv/bin/gunicorn bufet_project.wsgi:application --bind 0.0.0.0:8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable bufet
sudo systemctl start bufet
sudo systemctl status bufet
```

## Deactivate Virtual Environment

```bash
deactivate
```
