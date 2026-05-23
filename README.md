# MasteryGrid

MasteryGrid is an AI-powered assignment and assessment platform for Nigerian senior secondary schools. The MVP focuses on JAMB-style objective assignments: teachers log taught topics, generate assignments from an approved question bank, students answer online, the system auto-marks, and teachers see weak students and weak topics.

## Backend Stack

- Django
- Django REST Framework
- PostgreSQL
- JWT authentication with `djangorestframework-simplejwt`
- `django-environ` for environment variables
- `django-cors-headers`
- `django-filter`
- `drf-spectacular`
- WhiteNoise

The backend is a modular monolith located in `backend/`.

## Backend Setup

From the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements\dev.txt
```

Create your local environment file:

```powershell
Copy-Item .env.example .env
```

Update `.env` with your local PostgreSQL credentials.

## Environment Variables

Required variables are documented in `backend/.env.example`:

- `DJANGO_ENV`
- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`
- `DATABASE_NAME`
- `DATABASE_USER`
- `DATABASE_PASSWORD`
- `DATABASE_HOST`
- `DATABASE_PORT`
- `JWT_ACCESS_TOKEN_LIFETIME_MINUTES`
- `JWT_REFRESH_TOKEN_LIFETIME_DAYS`

## Database Setup

Create a local PostgreSQL database and user matching your `.env` values. Example:

```sql
CREATE DATABASE masterygrid;
CREATE USER masterygrid_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE masterygrid TO masterygrid_user;
```

## Important Migration Boundary

Do not run the first real migration until the custom `accounts.User` model is implemented.

The next backend step should add:

```python
AUTH_USER_MODEL = "accounts.User"
```

to settings and define the custom user model before running `makemigrations` or `migrate`.

## Useful Commands

Run Django checks:

```powershell
python manage.py check
```

After the custom user model is implemented, create and apply migrations:

```powershell
python manage.py makemigrations
python manage.py migrate
```

Run the development server:

```powershell
python manage.py runserver
```

## Demo Data

For pilot testing, seed a complete demo school with known logins:

```powershell
cd backend
.\venv\Scripts\python.exe manage.py seed_demo_data --with-submissions
```

See [docs/DEMO_DATA.md](docs/DEMO_DATA.md) for credentials and the recommended
test flow.

## Question Import

Trusted JAMB/past-exam questions can be imported into the question bank as draft
questions for review. See [docs/QUESTION_IMPORT.md](docs/QUESTION_IMPORT.md) for
the CSV format and workflow.

## AI Question Intelligence

AI can suggest topic tags, difficulty, explanations, and quality warnings for
existing question-bank items without auto-approving or generating student-facing
questions. See [docs/AI_QUESTION_INTELLIGENCE.md](docs/AI_QUESTION_INTELLIGENCE.md).

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for Render/Railway backend setup,
Vercel frontend setup, required environment variables, and the production safety
checklist.

## API Documentation

When the server is running:

- Schema: `http://127.0.0.1:8000/api/schema/`
- Swagger UI: `http://127.0.0.1:8000/api/docs/`
