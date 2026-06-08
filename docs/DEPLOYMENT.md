# MasteryGrid Deployment Guide

This guide prepares the current MVP for:

- Backend: Render or Railway
- Database: Managed PostgreSQL
- Frontend: Vercel
- Static files: WhiteNoise
- Media files: local filesystem for now

Official platform references:

- Render Django deployment: https://render.com/docs/deploy-django
- Railway Django guide: https://docs.railway.com/guides/django
- Railway PostgreSQL: https://docs.railway.com/databases/postgresql
- Vercel environment variables: https://vercel.com/docs/environment-variables
- Next.js environment variables: https://nextjs.org/docs/14/pages/building-your-application/configuring/environment-variables

## Backend Commands

Run from the `backend` directory.

Build command:

```bash
pip install -r requirements/prod.txt && python manage.py collectstatic --noinput
```

Start command:

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

Migration command:

```bash
python manage.py migrate
```

Optional demo seed command:

```bash
python manage.py seed_demo_data --with-submissions
```

## Required Backend Environment Variables

Use `backend/.env.production.example` as a template. Do not commit real values.

```text
DJANGO_ENV=prod
SECRET_KEY=<strong random secret>
DEBUG=False
ALLOWED_HOSTS=<backend-hosts-without-protocol>
CORS_ALLOWED_ORIGINS=<frontend-origins-with-protocol>
CSRF_TRUSTED_ORIGINS=<trusted-origins-with-protocol>
FRONTEND_URL=<frontend-origin>
DATABASE_URL=<managed-postgres-url>
DATABASE_NAME=<database name>
DATABASE_USER=<database user>
DATABASE_PASSWORD=<database password>
DATABASE_HOST=<database host>
DATABASE_PORT=5432
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=15
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
DEFAULT_FROM_EMAIL=MasteryGrid <noreply@your-domain.com>
AI_GENERATION_ENABLED=False
OPENAI_API_KEY=<required-only-if-ai-generation-is-enabled>
```

`DATABASE_URL` is also supported. If your host provides it, you can set that
instead of the split `DATABASE_*` variables.

AI suggestions are optional. Keep `AI_GENERATION_ENABLED=False` unless
`OPENAI_API_KEY` and AI usage limits are configured intentionally.

## CORS, CSRF, And Hosts

`ALLOWED_HOSTS` must contain backend hostnames only:

```text
ALLOWED_HOSTS=masterygrid-api.onrender.com,api.your-domain.com
```

`CORS_ALLOWED_ORIGINS` must contain frontend origins with protocol:

```text
CORS_ALLOWED_ORIGINS=https://masterygrid.vercel.app,https://app.your-domain.com
```

`CSRF_TRUSTED_ORIGINS` must contain HTTPS origins that submit browser requests
to Django, including the backend admin host and frontend host:

```text
CSRF_TRUSTED_ORIGINS=https://masterygrid-api.onrender.com,https://masterygrid.vercel.app
```

Keep local development values in local `.env`, not production:

```text
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

## Render Backend

1. Create a managed PostgreSQL database on Render.
2. Create a new Web Service from the repository.
3. If deploying from the monorepo, set the root directory to `backend`.
4. Set the environment to Python.
5. Set the build command:

   ```bash
   pip install -r requirements/prod.txt && python manage.py collectstatic --noinput
   ```

6. Set the start command:

   ```bash
   gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
   ```

7. Add all backend environment variables from
   `backend/.env.production.example`.
8. Set `ALLOWED_HOSTS` to the Render backend hostname and any custom API domain.
9. Set `CORS_ALLOWED_ORIGINS` to the Vercel frontend URL.
10. Set `CSRF_TRUSTED_ORIGINS` to the backend and frontend HTTPS origins.
11. Deploy the service.
12. Run migrations from Render Shell or a pre-deploy/release command:

    ```bash
    python manage.py migrate
    ```

13. Create a superuser:

    ```bash
    python manage.py createsuperuser
    ```

14. For demo/pilot environments only, seed demo data:

    ```bash
    python manage.py seed_demo_data --with-submissions
    ```

## Railway Backend Alternative

1. Create a Railway project.
2. Add a PostgreSQL database.
3. Add a backend service from the repository.
4. If deploying from the monorepo, set the service root directory to `backend`.
5. Set environment variables from `backend/.env.production.example`.
6. Use Railway's provided `DATABASE_URL`, or map the PostgreSQL variables to
   `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_HOST`, and
   `DATABASE_PORT`.
7. Set the build command:

   ```bash
   pip install -r requirements/prod.txt && python manage.py collectstatic --noinput
   ```

8. Set the start command:

   ```bash
   gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
   ```

9. Deploy.
10. Run migrations:

    ```bash
    python manage.py migrate
    ```

11. Create a superuser:

    ```bash
    python manage.py createsuperuser
    ```

## Vercel Frontend

1. Create a Vercel project from the repository.
2. Set the root directory to `frontend`.
3. Use the install command:

   ```bash
   npm install
   ```

4. Use the build command:

   ```bash
   npm run build
   ```

5. Set the production environment variable:

   ```text
   NEXT_PUBLIC_API_BASE_URL=https://your-backend-host/api
   NEXT_PUBLIC_ENABLE_DEMO_MODE=false
   ```

6. Deploy.
7. Copy the Vercel production URL into backend `CORS_ALLOWED_ORIGINS` and
   `CSRF_TRUSTED_ORIGINS`, then redeploy the backend if needed.

Keep `NEXT_PUBLIC_ENABLE_DEMO_MODE=false` for real production. Enable it only on
local, staging, preview, or disposable demo deployments.

## Post-Deploy Checklist

1. Run migrations:

   ```bash
   python manage.py migrate
   ```

2. Create a superuser or school admin:

   ```bash
   python manage.py createsuperuser
   ```

3. Confirm health:

   ```bash
   curl https://your-backend-host/api/health/
   ```

4. Log in as school admin and open `/admin/setup`.
5. Import or approve at least one trusted question-bank question.
6. Publish and submit a short assignment.
7. Start and submit one practice session.
8. Run smoke E2E against the deployed URLs:

   ```bash
   npm run e2e:smoke
   ```

Run the full seeded E2E suite only against local, staging, preview, or demo
tenants. Full seeded tests create data.

## Common Deployment Errors

- `DisallowedHost`: add the backend hostname to `ALLOWED_HOSTS` without
  `https://`.
- Browser CORS error: add the exact frontend origin to `CORS_ALLOWED_ORIGINS`
  with `https://`.
- CSRF failure in Django admin: add the backend/admin HTTPS origin to
  `CSRF_TRUSTED_ORIGINS`.
- Missing `SECRET_KEY`: set a strong production secret and keep it out of git.
- Database connection error: verify database host, port, username, password,
  database name, and whether your provider expects `DATABASE_URL`.
- Static files not loading: confirm `collectstatic` ran during build and
  WhiteNoise is installed.
- Tables missing: run `python manage.py migrate`.
- Frontend cannot reach backend: check `NEXT_PUBLIC_API_BASE_URL`, backend
  uptime, and CORS settings.
- Mixed HTTP/HTTPS issues: use HTTPS backend and frontend URLs in production.
- SSL redirect loop: confirm the platform forwards `X-Forwarded-Proto`; if
  needed for debugging, temporarily set `SECURE_SSL_REDIRECT=False`.
- Media files disappear after redeploy: local media storage is temporary on many
  platforms. Use persistent disks or cloud storage before relying on uploads.
- Demo login panel appears in production: set
  `NEXT_PUBLIC_ENABLE_DEMO_MODE=false` and rebuild the frontend.
- AI suggestion request fails: confirm `AI_GENERATION_ENABLED=True` and
  `OPENAI_API_KEY` are both configured.

## Production Safety Checklist

- `DEBUG=False`
- Strong `SECRET_KEY`
- Production PostgreSQL database configured
- `ALLOWED_HOSTS` set to backend domains
- `CORS_ALLOWED_ORIGINS` set to frontend domains
- `CSRF_TRUSTED_ORIGINS` set to backend/admin and frontend HTTPS origins
- `SECURE_SSL_REDIRECT=True` once HTTPS is confirmed
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- Migrations applied
- `collectstatic` completed
- Superuser created
- Admin password changed from any demo/default value
- Demo data not used in real production unless intentional
- `NEXT_PUBLIC_API_BASE_URL` points to production backend `/api`
- `NEXT_PUBLIC_ENABLE_DEMO_MODE=false` for real production
- Backend `/api/docs/` loads after authentication/host setup as expected
- Backend `/api/health/` returns `status=ok` and `database=ok`

## Known MVP Limitations

- No parent portal yet.
- No email, SMS, WhatsApp, or push notifications yet; notifications are in-app.
- Local media uploads on Render/Railway-style ephemeral filesystems are not
  durable. Use persistent disks or cloud storage before relying on uploaded
  question diagrams in production.
- AI question intelligence is an admin/teacher support layer for existing
  question-bank items. It is not student-facing question generation.
- Full seeded E2E tests create data and should run only on local, staging,
  preview, or disposable demo tenants.
