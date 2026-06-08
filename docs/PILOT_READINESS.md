# MasteryGrid Pilot Readiness

Use this checklist before a school demo, staging pilot, or first live rollout.
It focuses on reliability and repeatability rather than new product features.

## Required Environment

Backend:

- `DJANGO_ENV`
- `SECRET_KEY`
- `DATABASE_URL`
- `ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- `FRONTEND_URL`
- `DEFAULT_FROM_EMAIL`
- `DEBUG=false` for deployed environments
- `AI_GENERATION_ENABLED`
- `OPENAI_API_KEY` only if AI support features are enabled

Frontend:

- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_ENABLE_DEMO_MODE=false` for real production

Do not place real secrets in the frontend or in committed `.env` files.

## Deploy Checklist

1. Deploy the backend and frontend from the intended branch.
2. Run backend migrations:

   ```powershell
   python manage.py migrate
   ```

3. Confirm the backend health endpoint:

   ```powershell
   Invoke-WebRequest https://your-backend.example.com/api/health/
   ```

4. Create or confirm a school admin account.
5. For demo environments only, seed demo data if desired:

   ```powershell
   python manage.py seed_demo_data --with-submissions
   ```

6. Log in as school admin and open `/admin/setup`.
7. Complete or review the setup wizard steps:

   - academic session
   - term
   - class levels and class arms
   - subjects and topics
   - teachers and students
   - teacher assignments and student enrollments
   - approved question bank questions

8. Import a small trusted question CSV or ZIP and approve at least one question.
9. Publish a short assignment and submit it as a student.
10. Start and submit one practice session.
11. Confirm `NEXT_PUBLIC_ENABLE_DEMO_MODE=false` for real production. Enable it
    only for staging/demo walkthroughs.

## Smoke Verification

Run the quick E2E smoke suite after deployment:

```powershell
cd frontend
$env:E2E_FRONTEND_BASE_URL="https://your-frontend.example.com"
$env:E2E_BACKEND_API_URL="https://your-backend.example.com/api"
$env:E2E_ADMIN_EMAIL="admin@example.com"
$env:E2E_ADMIN_PASSWORD="..."
$env:E2E_TEACHER_EMAIL="teacher@example.com"
$env:E2E_TEACHER_PASSWORD="..."
$env:E2E_STUDENT_EMAIL="student@example.com"
$env:E2E_STUDENT_PASSWORD="..."
npm.cmd run e2e:smoke
```

The smoke suite checks `/api/health/`, the login page, and role logins. Run the
full seeded E2E suite only against local, staging, preview, or disposable demo
tenants.

## Cleanup

Seeded E2E tests leave data behind for debugging. On staging/demo, first dry-run:

```powershell
python manage.py cleanup_e2e_data
```

Then delete only after reviewing the plan:

```powershell
python manage.py cleanup_e2e_data --older-than-days 7 --confirm
```

GitHub Actions also has a manual **E2E Cleanup** workflow. Run dry-run first,
inspect logs, then run confirm only for disposable staging/demo data.

## Common Production Issues

- Backend CORS does not include the deployed frontend origin.
- Frontend `NEXT_PUBLIC_API_BASE_URL` points to an old backend URL.
- Render service is asleep when the first request arrives.
- Migrations were not run after deployment.
- No approved active questions exist, so practice and assignment generation are
  empty.
- School setup is incomplete, so dropdowns and analytics appear sparse.
- Local uploaded media on Render is temporary. Use local media only for MVP demos
  and plan cloud storage for durable production media.
- E2E seeded tests were run against a real tenant and created extra records.
- Demo mode was enabled on a real production frontend. Disable
  `NEXT_PUBLIC_ENABLE_DEMO_MODE` and rebuild.
- AI suggestions are enabled without `OPENAI_API_KEY`.

## Safe Defaults

- Imported questions remain draft until approved.
- Health check exposes status only, not secrets.
- Full seeded E2E is manual/protected in GitHub Actions.
- Cleanup is dry-run by default and requires `--confirm`.
- Demo mode is disabled unless `NEXT_PUBLIC_ENABLE_DEMO_MODE=true`.

## Known MVP Limitations

- No parent portal yet.
- No email, SMS, WhatsApp, or push notifications yet.
- Local uploaded media on Render/Railway-style filesystems is not durable.
- AI question intelligence supports existing question-bank review only; it does
  not generate student-facing questions.
- Full seeded E2E creates data and should use staging/demo tenants only.
