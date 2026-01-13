# Bufet Web - Django Application

A Django web application for managing a buffet/cafeteria.

## Setup Instructions

### 1. Activate Virtual Environment

```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Run Migrations

```powershell
python manage.py migrate
```

### 4. Create Superuser (Admin)

```powershell
python manage.py createsuperuser
```

### 5. Run Development Server

```powershell
python manage.py runserver
```

The application will be available at: http://127.0.0.1:8000/

Admin panel: http://127.0.0.1:8000/admin/

## Project Structure

- `bufet_project/` - Django project settings
- `main/` - Main application
- `manage.py` - Django management script
- `venv/` - Virtual environment
- `requirements.txt` - Python dependencies

## Development

To deactivate the virtual environment:
```powershell
deactivate
```
