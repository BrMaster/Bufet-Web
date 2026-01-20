# Bufet Web - Django Application

A Django web application for managing a buffet/cafeteria with camera access feature.

## Features
- Landing page with login button
- Camera access on login
- HTTPS support for secure local development

## Windows Setup Instructions

### 1. Create Virtual Environment

```powershell
python -m venv venv
```

### 2. Activate Virtual Environment

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Run Migrations

```powershell
python manage.py migrate
```

### 5. Create Superuser (Admin) - Optional

```powershell
python manage.py createsuperuser
```

### 6. Create HTTPS Certificates (For Camera Access)

Download mkcert from [https://github.com/FiloSottile/mkcert/releases](https://github.com/FiloSottile/mkcert/releases) and run:

```powershell
mkcert -install
mkcert localhost 127.0.0.1 192.168.x.x  # Replace with your IP
```

### 7. Run Development Server

```powershell
python manage.py runserver_plus 0.0.0.0:8000 --cert-file localhost+2.pem --key-file localhost+2-key.pem
```

Or for port 26105:

```powershell
python manage.py runserver_plus 0.0.0.0:26105 --cert-file localhost+2.pem --key-file localhost+2-key.pem
```

The application will be available at: https://localhost:8000/ or https://localhost:26105/

Admin panel: https://localhost:8000/admin/

## Project Structure

- `bufet_project/` - Django project settings and URL configuration
- `main/` - Main application with views and URL routing
- `templates/` - HTML templates (home.html, logged_in.html)
- `manage.py` - Django management script
- `venv/` - Virtual environment
- `requirements.txt` - Python dependencies
- `db.sqlite3` - SQLite database
- `localhost+2.pem` / `localhost+2-key.pem` - HTTPS certificates

## Dependencies

- Django 6.0.1+ - Web framework
- django-extensions - Extended management commands including runserver_plus
- Werkzeug - WSGI toolkit for development server
- pyOpenSSL - SSL/TLS support for HTTPS

## Development

To deactivate the virtual environment:
```powershell
deactivate
```
