# MasteryGrid E2E Testing

MasteryGrid uses Playwright for browser-level smoke and workflow tests. The E2E
suite lives in `frontend/e2e` and can run against local development, staging, or
deployed demo environments.

## Install

From `frontend/`:

```powershell
npm.cmd install
npx playwright install
```

## Environment

Copy the example values when you need a local E2E env file:

```powershell
Copy-Item .env.e2e.example .env.e2e
```

`playwright.config.ts` loads `frontend/.env.e2e` automatically when the file
exists. Shell environment variables still take precedence.

Required variables:

```env
E2E_FRONTEND_BASE_URL=http://127.0.0.1:3000
E2E_BACKEND_API_URL=http://127.0.0.1:8000/api

E2E_ADMIN_EMAIL=admin@masterygrid.demo
E2E_ADMIN_PASSWORD=Password123!
E2E_TEACHER_EMAIL=teacher@masterygrid.demo
E2E_TEACHER_PASSWORD=Password123!
E2E_STUDENT_EMAIL=student1@masterygrid.demo
E2E_STUDENT_PASSWORD=Password123!

E2E_TEST_PASSWORD=Password123!
E2E_ALLOW_PRODUCTION=false
```

Do not commit real credentials. The example credentials are intended for seeded
demo or staging data.

## Local Run

Start the backend and frontend first:

```powershell
cd backend
.\venv\Scripts\python.exe manage.py seed_demo_data --with-submissions
.\venv\Scripts\python.exe manage.py runserver
```

In another terminal:

```powershell
cd frontend
npm.cmd run dev
```

Then run:

```powershell
cd frontend
npm.cmd run e2e
```

Useful variants:

```powershell
npm.cmd run e2e:headed
npm.cmd run e2e:ui
npm.cmd run e2e:report
```

For one spec in headed mode:

```powershell
npm.cmd run e2e:headed -- e2e/tests/01-auth-smoke.spec.ts
```

Open the last HTML report:

```powershell
npm.cmd run e2e:report
```

When a test fails, Playwright keeps screenshots, videos, and trace data according
to `playwright.config.ts`. Open the report and select the failed test to inspect
the page snapshot, network events, console output, and trace attachment.

## Deployed Run

Set URLs and credentials for the deployed demo or staging environment:

```powershell
$env:E2E_FRONTEND_BASE_URL="https://your-vercel-app.vercel.app"
$env:E2E_BACKEND_API_URL="https://your-render-service.onrender.com/api"
$env:E2E_ADMIN_EMAIL="admin@masterygrid.demo"
$env:E2E_ADMIN_PASSWORD="Password123!"
$env:E2E_TEACHER_EMAIL="teacher@masterygrid.demo"
$env:E2E_TEACHER_PASSWORD="Password123!"
$env:E2E_STUDENT_EMAIL="student1@masterygrid.demo"
$env:E2E_STUDENT_PASSWORD="Password123!"
npm.cmd run e2e
```

Avoid running future mutating tests against real production data. The helper in
`e2e/utils/env.ts` blocks production-like mutating test targets unless
`E2E_ALLOW_PRODUCTION=true` is set intentionally. URLs containing `staging`,
`stage`, `demo`, or `preview` are treated as non-production E2E targets.

## GitHub Actions

MasteryGrid has two CI workflows:

- `.github/workflows/ci.yml` runs safe checks on every push or pull request to
  `main`.
- `.github/workflows/e2e.yml` runs Playwright against deployed or staging URLs
  when E2E secrets are configured.

The default CI workflow runs:

- backend dependency install
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- frontend `npm ci`
- frontend `npm run type-check`
- frontend `npm run lint`
- frontend `npm run build`

The backend job uses a disposable PostgreSQL service inside GitHub Actions. It
does not use production database credentials.

### E2E Secrets

Configure these repository secrets before running the E2E workflow:

```text
E2E_FRONTEND_BASE_URL
E2E_BACKEND_API_URL
E2E_ADMIN_EMAIL
E2E_ADMIN_PASSWORD
E2E_TEACHER_EMAIL
E2E_TEACHER_PASSWORD
E2E_STUDENT_EMAIL
E2E_STUDENT_PASSWORD
E2E_TEST_PASSWORD
E2E_ALLOW_PRODUCTION
```

`E2E_TEST_PASSWORD` is used for newly created test users in seeded workflows.
`E2E_ALLOW_PRODUCTION` should stay `false` unless you intentionally want seeded
tests to create data against a production-like target.

### E2E Workflow Modes

The E2E workflow can run in two modes:

- `smoke`: runs only `01-auth-smoke.spec.ts`.
- `full`: runs `01`, `02`, `03`, `04`, `05`, `06`, `07`, `08`, `09`, `10`, and `11`, including
  seeded/mutating tests.

Pushes to `main` run smoke E2E only when the required secrets exist. If secrets
are missing, the workflow prints a clear skip message and exits successfully.

To run the full seeded suite:

1. Open the GitHub Actions tab.
2. Select **E2E Tests**.
3. Click **Run workflow**.
4. Choose `full`.

Full seeded tests run only when `E2E_ALLOW_PRODUCTION=true` or when the target
URLs clearly look like staging/demo/preview/local. Seeded tests create school,
user, question, question-import, practice, and assignment data, so use a
disposable demo tenant.

### Playwright Artifacts

The E2E workflow uploads `frontend/playwright-report/` and
`frontend/test-results/` as the `playwright-artifacts` artifact. Download it from
the workflow run to inspect screenshots, videos, traces, and error context.

## API-Assisted Setup

Seeded E2E tests use backend APIs to prepare disposable test data, then verify
the workflow through the browser. This keeps setup fast while still testing the
real user experience.

The reusable setup helper is `frontend/e2e/utils/seed.ts`. It logs in with the
admin credentials, creates uniquely named records, and returns generated teacher
and student credentials for the test run.

The current seed creates:

- academic session, term, class level, and class arm
- subject and topic
- teacher and student users
- teacher class/subject assignment
- student enrollment
- question source when the API role allows source creation
- five approved question-bank questions
- one published teacher assignment

Seeded records use names/emails like:

```text
e2e.teacher.<runId>@masterygrid.test
e2e.student.<runId>@masterygrid.test
E2E Physics <runId>
E2E Motion <runId>
```

The setup is idempotent by uniqueness, not cleanup. It does not delete test
data, so run it against local, staging, or a deployed demo environment only.

For clean school scoping, `E2E_ADMIN_EMAIL` should be a `school_admin` account.
If the credentials belong to a `platform_admin` without a school, seeded setup
will fail clearly because the current backend does not expose a school creation
API.

Question sources are currently read-only for school admins. The setup helper
tries to create a source, but if the API returns permission denied it continues
with source-less school questions because the question model allows `source=null`.

Run the seeded practice setup test:

```powershell
cd frontend
npm.cmd run e2e -- e2e/tests/02-seeded-practice-setup.spec.ts
```

## Cleaning E2E Data

Seeded tests deliberately leave data behind after failures so you can inspect the
school, users, imports, assignments, practice sessions, and media that caused the
failure. Over time, local/staging/demo databases can accumulate many records with
`E2E` names and `@masterygrid.test` users.

Use the backend cleanup command to review and remove only clearly identifiable
E2E-generated records. It is dry-run by default:

```powershell
cd backend
.\venv\Scripts\python.exe manage.py cleanup_e2e_data
```

Delete all matched E2E data in a local/staging/demo database:

```powershell
.\venv\Scripts\python.exe manage.py cleanup_e2e_data --confirm
```

Delete one failed run by run id:

```powershell
.\venv\Scripts\python.exe manage.py cleanup_e2e_data --run-id mpjqjt6py5jjq --confirm
```

Delete only older test data:

```powershell
.\venv\Scripts\python.exe manage.py cleanup_e2e_data --older-than-days 7 --confirm
```

Useful optional scope:

```powershell
.\venv\Scripts\python.exe manage.py cleanup_e2e_data --school-id 1 --confirm
```

The command refuses destructive cleanup when `DJANGO_ENV=prod` or `DEBUG=False`
unless `--allow-production` is provided. Use that flag only for an intentional
cleanup of a disposable staging/demo tenant:

```powershell
.\venv\Scripts\python.exe manage.py cleanup_e2e_data --confirm --allow-production
```

Safety rules:

- E2E users are matched only by emails ending in `@masterygrid.test`.
- Demo users like `admin@masterygrid.demo` are not matched by user cleanup.
- Domain records are matched by explicit `E2E` names/titles/text or by links to
  matched E2E users, questions, assignments, imports, subjects, topics, classes,
  or sessions.
- The command prints a deletion plan before deleting and uses a transaction for
  confirmed cleanup.
- E2E tests do not auto-delete data by default.

### Manual Cleanup in GitHub Actions

The repository includes `.github/workflows/e2e-cleanup.yml`, a manual-only
workflow named **E2E Cleanup**. It never runs on push or pull request.

Configure these GitHub repository or environment secrets before using it:

```text
CLEANUP_DATABASE_URL
SECRET_KEY
```

Optional secrets:

```text
ALLOWED_HOSTS
CORS_ALLOWED_ORIGINS
CSRF_TRUSTED_ORIGINS
```

Recommended process:

1. Open the GitHub Actions tab.
2. Select **E2E Cleanup**.
3. Click **Run workflow**.
4. Choose `mode=dry-run` and add any filters.
5. Inspect the deletion plan in the workflow logs.
6. Run again with `mode=confirm` only if the dry-run output is safe.

Useful workflow inputs:

- `run_id`: clean one failed run, for example `mpjqjt6py5jjq`.
- `older_than_days`: clean accumulated E2E data older than a threshold, for
  example `7`.
- `school_id`: restrict cleanup to one school.
- `environment_name`: choose the GitHub environment that holds the staging/demo
  cleanup secrets.
- `allow_production`: passes `--allow-production` to the management command.

Examples:

- Clean one failed run: run dry-run with `run_id=<runId>`, inspect the logs, then
  rerun with `mode=confirm`.
- Clean old staging data: run dry-run with `older_than_days=7`, inspect the logs,
  then rerun with `mode=confirm`.
- Restrict cleanup: add `school_id=<id>` when a staging database has multiple
  demo tenants.

The workflow sets `DJANGO_ENV=prod` so it behaves like deployed settings. In
confirmed mode, the backend command will still refuse cleanup unless
`allow_production=true` is selected. Do not use `allow_production=true` casually;
reserve it for disposable staging/demo databases where you have already reviewed
the dry-run output.

## Current Coverage

The first suite is `e2e/tests/01-auth-smoke.spec.ts`:

- school admin can log in and reaches `/admin/dashboard`
- teacher can log in and reaches `/teacher/dashboard`
- student can log in and reaches `/student/dashboard`
- wrong password shows an error and stays on login

The first seeded suite is `e2e/tests/02-seeded-practice-setup.spec.ts`:

- creates the minimum school-scoped workflow data through API setup
- logs in as the generated student by API and browser storage
- opens Practice and verifies the seeded subject/topic are selectable

The seeded suite uses `loginByApiAndStorage` because login itself is already
covered by `01-auth-smoke.spec.ts`. This keeps workflow tests focused on setup
and page behavior instead of repeatedly exercising the login form.

Additional seeded workflow suites:

- `03-student-practice-flow.spec.ts`: student starts practice, submits answers,
  reviews result, and sees practice analytics.
- `04-assignment-flow.spec.ts`: teacher creates/publishes an assignment, student
  submits it, and teacher sees results.
- `05-question-import-flow.spec.ts`: admin validates/imports a synthetic CSV,
  opens an imported draft question, approves it, and finds it in the approved
  question bank.
- `06-zip-diagram-import-flow.spec.ts`: admin validates/imports a synthetic ZIP
  with a generated PNG diagram, approves the question, and verifies the diagram
  appears in student practice attempt and result views.
- `07-learning-path-flow.spec.ts`: student completes low-score practice, follows
  the guided learning path into recommended practice, and reviews the result.
- `08-teacher-remediation-flow.spec.ts`: student submits a low-score assignment,
  teacher opens remediation recommendations, creates a remedial assignment, and
  publishes it.
- `09-admin-intervention-dashboard.spec.ts`: student submits a low-score
  assignment, school admin opens the intervention dashboard, sees class,
  subject, teacher, and weak-cluster recommendations, and follows an analytics
  action link.
- `10-student-progress-report.spec.ts`: student completes assignment and
  practice work, then school admin and teacher open the internal progress report
  with assignment, practice, weak-topic, and recommendation sections.
- `11-student-progress-print.spec.ts`: school admin and teacher open the
  printable progress report view, verify print/export controls, and confirm the
  report can navigate back to the normal view.

## Login Debugging

The UI login helper waits for `/api/auth/token/`, captures its status/body, then
waits for `/api/auth/me/` and the role dashboard redirect. If login stays on
`/login`, the thrown error includes:

- current URL
- visible login/error text
- redacted auth-related localStorage keys
- token and current-user API response details
- failed requests
- console errors and page errors
- screenshot path under `frontend/test-results/login-debug`
- visible page text

Common login failure causes:

- `NEXT_PUBLIC_API_BASE_URL` points to the wrong backend
- backend CORS does not include the frontend test origin
- backend is not running or deployed backend is sleeping
- frontend is not running
- stale `.next` after running `next build` while `next dev` is still running
- generated test user belongs to a previous or different backend database
- wrong E2E credentials in shell vars or `.env.e2e`

Future suites should cover imports, approvals, practice submission, assignments,
and analytics on disposable demo/staging data.
