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
- `full`: runs `01`, `02`, `03`, and `04`, including seeded/mutating tests.

Pushes to `main` run smoke E2E only when the required secrets exist. If secrets
are missing, the workflow prints a clear skip message and exits successfully.

To run the full seeded suite:

1. Open the GitHub Actions tab.
2. Select **E2E Tests**.
3. Click **Run workflow**.
4. Choose `full`.

Full seeded tests run only when `E2E_ALLOW_PRODUCTION=true` or when the target
URLs clearly look like staging/demo/preview/local. Seeded tests create school,
user, question, practice, and assignment data, so use a disposable demo tenant.

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
