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

## Manual Startup - Development

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

## HTTPS with mkcert (For Camera Access)

```bash
# Install mkcert
sudo apt-get install libnss3-tools  # For Linux
# or use brew on macOS: brew install mkcert
# or download from https://github.com/FiloSottile/mkcert/releases

# Create local CA and certificate
mkcert -install
mkcert localhost 127.0.0.1 192.168.x.x  # Replace with your IP

# Run development server with HTTPS
python manage.py runserver_plus 0.0.0.0:8000 --cert-file localhost+2.pem --key-file localhost+2-key.pem
```

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

## Dependencies

- Django 6.0.1+ - Web framework
- django-extensions - Extended management commands including runserver_plus
- Werkzeug - WSGI toolkit for development server
- pyOpenSSL - SSL/TLS support for HTTPS

## Deactivate Virtual Environment

```bash
deactivate
```
